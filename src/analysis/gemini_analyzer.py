"""Gemini vision analysis for Sherpa."""
import google.generativeai as genai
import json
from typing import Dict
from datetime import datetime

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        """Initialize Gemini analyzer."""
        genai.configure(api_key=api_key)

        # Configure generation parameters for better JSON responses
        generation_config = {
            "temperature": 0.1,  # Lower temperature for more consistent JSON
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

        # Configure safety settings to be less restrictive for screenshots
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        self.current_task = "No task set"
        self.distraction_count = 0
        self.last_analysis = None

    def set_task(self, task: str):
        """Set the current task user should be working on."""
        self.current_task = task
        self.distraction_count = 0
        print(f"🎯 Task set: {task}")

    def analyze_screenshot(self, image_bytes: bytes) -> Dict:
        """
        Analyze screenshot to determine if user is on-task.

        Args:
            image_bytes: PNG image as bytes

        Returns:
            Dictionary with analysis results
        """
        prompt = f"""You are Sherpa, an AI productivity mentor analyzing a user's screen.

Current Task: "{self.current_task}"
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Analyze this screenshot and respond in JSON format:

{{
    "activity_detected": "Brief description of what's visible on screen",
    "is_on_task": true/false,
    "confidence": "high/medium/low",
    "reasoning": "One sentence explaining your assessment",
    "app_or_website": "Name of primary application or website visible",
    "needs_intervention": true/false
}}

Guidelines for determining if on-task:
- If the task is "No task set", mark is_on_task as true
- For task "Coding": Only coding environments (IDE, terminal, GitHub, Stack Overflow, documentation) are on-task
- For task "Writing": Only writing apps (docs, editors, research) are on-task
- Social media (Reddit, Twitter, Instagram, Facebook, TikTok) is ALWAYS off-task unless the task explicitly involves social media
- Shopping (Amazon, eBay, etc.) is ALWAYS off-task unless the task explicitly involves shopping
- Entertainment (YouTube, Netflix, games) is ALWAYS off-task unless the task explicitly involves entertainment
- News sites, apartment browsing, sports sites = off-task unless directly related to stated task

Be strict:
- If browsing Reddit while task is "Coding" → is_on_task=false, needs_intervention=true
- If browsing apartments while task is "Coding" → is_on_task=false, needs_intervention=true
- If watching YouTube while task is "Writing" → is_on_task=false, needs_intervention=true

Respond ONLY with valid JSON, no other text."""

        try:
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_bytes}
            ])

            # Debug: Check response structure
            if not response or not hasattr(response, 'text'):
                print(f"❌ Invalid response structure: {response}")
                return self._default_analysis()

            response_text = response.text.strip()

            # Debug: Show what we received
            if not response_text:
                print(f"❌ Empty response from Gemini")
                print(f"   Prompt finish reason: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
                print(f"   Candidates: {len(response.candidates) if hasattr(response, 'candidates') else 0}")
                if hasattr(response, 'candidates') and response.candidates:
                    print(f"   Finish reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
                    if hasattr(response.candidates[0], 'safety_ratings'):
                        print(f"   Safety ratings: {response.candidates[0].safety_ratings}")
                return self._default_analysis()

            # Clean response text (remove markdown code blocks if present)
            if response_text.startswith("```"):
                # Remove ```json and ``` markers
                lines = response_text.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = '\n'.join(lines).strip()

            result = json.loads(response_text)

            # Update distraction tracking
            if not result.get('is_on_task', True):
                self.distraction_count += 1
            else:
                self.distraction_count = max(0, self.distraction_count - 1)

            result['distraction_count'] = self.distraction_count
            result['timestamp'] = datetime.now().isoformat()

            self.last_analysis = result

            print(f"\n📊 Analysis: {result['activity_detected']}")
            print(f"   On-task: {result['is_on_task']} | Confidence: {result['confidence']}")
            print(f"   Distraction count: {self.distraction_count}")

            return result

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gemini response: {e}")
            return self._default_analysis()
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return self._default_analysis()

    def _default_analysis(self) -> Dict:
        """Return default analysis if API call fails."""
        return {
            "activity_detected": "Unknown",
            "is_on_task": True,
            "confidence": "low",
            "reasoning": "Analysis failed",
            "app_or_website": "Unknown",
            "needs_intervention": False,
            "distraction_count": self.distraction_count,
            "timestamp": datetime.now().isoformat()
        }

    def should_intervene(self) -> bool:
        """
        Decide if Sherpa should speak up.

        Returns:
            True if voice intervention is needed
        """
        if not self.last_analysis:
            return False

        # Intervention criteria:
        # - Marked as needs_intervention by Gemini
        # - OR distraction count >= 1 (immediate intervention on first distraction)
        return (
            self.last_analysis.get('needs_intervention', False) or
            self.distraction_count >= 1
        )

    def get_intervention_context(self) -> str:
        """Get context for voice agent intervention."""
        if not self.last_analysis:
            return "User seems distracted."

        return f"""The user said they're working on: "{self.current_task}"

However, I detected they're currently: {self.last_analysis['activity_detected']}

App/Website: {self.last_analysis['app_or_website']}
This has happened {self.distraction_count} times recently.

Your role: Gently ask them about what they're doing, be curious not judgmental."""
