# Sherpa AI - Your Productivity Coach

An AI-powered productivity assistant that monitors your screen activity and provides gentle voice interventions when you get distracted.

Built for the AI Tinkerers Gemini Pipecat Hackathon.

---

## Demo Video

[Demo Video - Watch Here] (60-120 seconds showing the product in action)

Note: The demo shows:

- Starting Sherpa and setting your task
- Screen monitoring in action
- Getting distracted (e.g., browsing Reddit)
- Sherpa detecting the distraction and speaking to you
- Voice conversation with Sherpa
- Getting back on task

---

## Hackathon Submission Details

### How We Used Gemini + Pipecat

Gemini 1.5 Flash (Vision):

- Analyzes screenshots every 60 seconds to understand what's on screen
- Processes multimodal input (image + task description + timestamp)
- Returns structured JSON indicating if user is on-task or distracted
- Provides intelligent context understanding (distinguishes research from distraction)

Gemini 2.0 Flash Experimental (LLM via Pipecat):

- Powers the conversational voice bot through Pipecat's GoogleLLMService
- Generates empathetic, contextual responses during interventions
- Maintains conversation history via LLMContextAggregatorPair
- Uses warm, supportive personality to help users get back on track

Pipecat AI Framework:

- Orchestrates the entire voice pipeline with modular processors
- Pipeline: LocalAudioInput → GoogleSTTService → LLMUserAggregator → GoogleLLMService (Gemini) → GoogleTTSService → LocalAudioOutput → LLMAssistantAggregator
- Handles Voice Activity Detection (VAD) with Silero for natural conversation flow
- Manages interruptions and conversation state automatically
- Enables local audio through PyAudio (no browser needed)

### Other Tools & Integrations

- Google Cloud Speech-to-Text: Converts user voice to text for Gemini LLM processing
- Google Cloud Text-to-Speech: Converts Gemini's responses to natural speech (en-US-Journey-D voice)
- mss (Multi-Screenshot): Fast, cross-platform screenshot capture library
- PyAudio: Local audio I/O for microphone input and speaker output
- Silero VAD: Voice Activity Detection to determine when user is speaking
- python-dotenv: Secure environment variable management for API keys
- loguru: Enhanced logging for debugging and monitoring

### What We Built During the Hackathon vs. Prior Work

Everything was built entirely during the hackathon (100% new):

- Complete Sherpa AI system from scratch
- Screen monitoring with Gemini Vision integration
- Distraction detection logic and intervention triggers
- Pipecat voice pipeline with local audio transport
- Integration of Gemini LLM for conversational AI
- System prompt engineering for supportive coach personality
- VAD tuning to prevent audio feedback loops
- Full error handling and graceful shutdown
- Comprehensive documentation and setup guides

No prior work or existing codebase - this was built from the ground up for this hackathon.

### Feedback on Tools Used

Gemini 1.5 Flash (Vision):

- Pros: Fast analysis (<1 second), perfect for real-time monitoring; strong context understanding that distinguishes task-related browsing from distraction; high rate limits (60 req/min) made development smooth
- Challenges: Needed to tune safety settings to prevent empty responses initially
- Suggestions: More examples in docs for structured JSON output with vision

Gemini 2.0 Flash Experimental (LLM via Pipecat):

- Pros: Works seamlessly with Pipecat's GoogleLLMService; generates natural, warm conversational responses; latest experimental model provides improved conversation quality
- Suggestions: Native streaming audio support would eliminate need for separate STT/TTS services

Pipecat AI:

- Pros: Made complex voice pipeline development straightforward; great documentation with clear examples for Google services; modular design makes it easy to swap components
- Challenges: Understanding frame flow and aggregators took some time; LLMMessagesFrame was deprecated mid-development which required adaptation
- Suggestions: More examples of local audio transport with VAD tuning would be helpful

Google Cloud STT/TTS:

- Pros: High quality, natural-sounding voice; reliable and consistent performance throughout development
- Challenges: Service account creation has many steps and can be complex for first-time users
- Suggestions: Simpler auth flow for hackathon/prototyping use cases

### Live Demo Link

Due to the nature of this application (requires screen recording permissions, local audio, and runs on user's machine), a traditional web demo isn't applicable. However, you can:

1. Clone the repo and run locally (15-minute setup)
2. Watch the demo video above
3. Review the comprehensive documentation below

---

## Features

- Screen Monitoring: Captures screenshots every 60 seconds to track your activity
- Vision Analysis: Uses Google Gemini 1.5 Flash with vision to analyze what you're doing
- Smart Detection: Distinguishes between on-task and distracted behavior with AI
- Local Voice Intervention: Speaks to you directly through your laptop speakers when distractions are detected
- Natural Conversation: Uses Pipecat AI with Google Speech-to-Text, Gemini LLM, and Google Text-to-Speech for fluid voice interactions
- Real-time Audio: No browser needed - audio plays directly through your speakers and listens through your microphone

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      SHERPA AI SYSTEM                        │
└─────────────────────────────────────────────────────────────┘

1. Screen Monitoring
   ┌──────────────────┐
   │ Screen Capture   │ → Takes screenshot every 60s using mss
   │    (mss)         │
   └────────┬─────────┘
            │ PNG image bytes
            ▼
2. Vision Analysis
   ┌──────────────────┐
   │ Gemini Vision    │ → Analyzes: What's on screen?
   │  (2.0 Flash)     │   Is user on-task? Distraction?
   └────────┬─────────┘
            │ JSON analysis
            ▼
3. Intervention Logic
   ┌──────────────────┐
   │  Analyzer        │ → Tracks distraction count
   │  should_intervene│ → Triggers after 1 distraction
   └────────┬─────────┘
            │ If distracted >= 1
            ▼
4. Voice Bot (Local Audio)
   ┌──────────────────────────────────────────────────┐
   │            Pipecat Pipeline                       │
   │                                                   │
   │  Microphone → STT → LLM Context → Gemini LLM     │
   │              (Google)              (2.0 Flash)    │
   │                                        ↓          │
   │  Speakers ← TTS ← Response ← ← ← ← ← ←          │
   │           (Google)                                │
   └──────────────────────────────────────────────────┘
```

### Detailed Architecture

#### 1. Screen Capture Layer

- Library: mss (multi-platform screenshot library)
- Frequency: Every 60 seconds
- Format: PNG image captured as bytes
- Privacy: Screenshots are never saved to disk

#### 2. Vision Analysis Layer

- Model: Google Gemini 1.5 Flash with vision capabilities
- Input:
  - Screenshot image (PNG bytes)
  - Current task description from user
  - Timestamp
- Output: JSON with:
  ```json
  {
    "activity_detected": "Brief description of screen content",
    "is_on_task": true/false,
    "confidence": "high/medium/low",
    "reasoning": "Why this assessment was made",
    "app_or_website": "Primary app visible",
    "needs_intervention": true/false
  }
  ```
- Smart Features:
  - Understands context (research, docs, thinking time = on-task)
  - Recognizes common distractions (social media, entertainment)
  - Considers task description for relevance

#### 3. Intervention Logic

- Triggers:
  - Gemini marks `needs_intervention: true` (clear distraction)
  - OR distraction count reaches 1 (immediate intervention)
- Distraction Tracking:
  - Off-task detection: `distraction_count += 1`
  - Back on-task: `distraction_count = max(0, count - 1)`
  - After intervention: Reset to `0`

#### 4. Voice Bot Pipeline (Pipecat + Google Services)

Transport: Local Audio (PyAudio)

- Captures audio from system microphone
- Plays audio through system speakers
- No browser or external apps needed

Pipeline Flow:

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipecat Pipeline                          │
│                                                              │
│  1. LocalAudioInput (Microphone)                            │
│     ↓                                                        │
│  2. GoogleSTTService (Speech-to-Text)                       │
│     ↓                                                        │
│  3. LLMUserAggregator (Add user message to context)         │
│     ↓                                                        │
│  4. GoogleLLMService (Gemini 1.5 Flash)                     │
│     ↓                                                        │
│  5. GoogleTTSService (Text-to-Speech)                       │
│     ↓                                                        │
│  6. LocalAudioOutput (Speakers)                             │
│     ↓                                                        │
│  7. LLMAssistantAggregator (Add bot response to context)    │
└─────────────────────────────────────────────────────────────┘
```

Voice Activity Detection (VAD):

- Uses Silero VAD model
- Detects when user starts/stops speaking
- Parameters tuned to prevent false interruptions:
  - stop_secs=1.0 - Wait 1 second of silence before considering speech done
  - min_volume=0.6 - Higher volume threshold to ignore ambient noise
  - confidence=0.7 - Higher confidence required to detect speech

Conversation System:

- System Prompt: Defines Sherpa's warm, supportive personality
- Context Management: Maintains conversation history with user
- LLM: Gemini 1.5 Flash generates contextual, empathetic responses
- TTS Voice: Google's en-US-Journey-D (natural, warm voice)

## Setup

### Prerequisites

- Python 3.10 or higher
- macOS (with Homebrew), Linux, or Windows
- Microphone and speakers
- Screen recording permissions

### 1. Install System Dependencies

macOS:

```bash
# Install portaudio (required for PyAudio)
brew install portaudio
```

Linux (Ubuntu/Debian):

```bash
sudo apt-get install portaudio19-dev
```

Windows:

- PyAudio wheels should install automatically

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get API Keys

#### Google AI API Key (Required)

For Gemini Vision and LLM:

1. Visit https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

#### Google Cloud Service Account (Required)

For Speech-to-Text and Text-to-Speech. You can use other alternatives like deepgram, elevenlabs etc. as well. I'm sticking entirely to google stuff here, keeping three separate instead of using google live api.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable APIs:
   - Go to "APIs & Services" > "Library"
   - Search and enable Cloud Speech-to-Text API
   - Search and enable Cloud Text-to-Speech API
4. Create Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name: sherpa-voice-bot
   - Grant roles:
     - Cloud Speech Client
     - Cloud Text-to-Speech Client
5. Create JSON Key:
   - Click on the service account
   - Go to "Keys" tab
   - "Add Key" > "Create new key" > "JSON"
   - Download the JSON file to your project directory

### 5. Configure Environment

Create a `.env` file in the project root:

```bash
# Google AI API Key (for Gemini Vision and LLM)
GOOGLE_API_KEY=your_google_ai_api_key_here

# Google Cloud Service Account (for STT and TTS)
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/your-service-account.json
```

Important: Replace the paths with your actual values!

### 6. Grant Screen Recording Permissions

macOS:

1. Go to System Settings → Privacy & Security → Screen Recording
2. Add Terminal (or your Python IDE)
3. Toggle the permission on

Linux/Windows:

- No special permissions typically required

### 7. Test the System

Run the test suite to verify everything works:

```bash
python test_sherpa.py
```

You should see:

- Screenshot captured
- Gemini analysis complete
- Multiple captures with distraction detection

### 8. Start Sherpa

```bash
python main.py
```

## Usage

### Starting Sherpa

When you run `python main.py`, Sherpa will:

1. Ask about your task:

```
🏔️  Welcome to Sherpa!

What are you working on today? Writing a blog post about AI
```

2. Begin monitoring:

```
============================================================
🏔️  SHERPA AI - Your Productivity Coach
============================================================
📸 Taking screenshots every 60 seconds
🎯 Current task: Writing a blog post about AI
============================================================
```

3. Show real-time analysis:

```
📊 Analysis: VSCode with Python file open
   On-task: True | Confidence: high
   Distraction count: 0
```

### When You Get Distracted

If Sherpa detects you're off-task:

```
📊 Analysis: Browsing Reddit
   On-task: False | Confidence: high
   Distraction count: 1

⚠️  INTERVENTION TRIGGERED!

🎤 SHERPA SPEAKING!
   Using your laptop's microphone and speakers

🎧 Listening through your microphone...
🔊 Speaking through your speakers...
```

Important: Use headphones to prevent audio feedback!

### Voice Conversation

Sherpa will speak to you with:

- Warm, supportive tone (not judgmental)
- Short responses (1-2 sentences)
- Genuine curiosity about what you're doing
- Helpful reflections to get you back on track

Example conversation:

```
Sherpa: "Hey! I noticed you might be off track. What are you working on right now?"
You: "I'm supposed to be coding but got distracted by Reddit"
Sherpa: "Gotcha. How does browsing Reddit connect to your coding work?"
You: "It doesn't, just procrastinating"
Sherpa: "I hear you. Want to get back to coding, or is something blocking you?"
```

### Stopping Sherpa

Press `Ctrl+C` to stop monitoring at any time. Sherpa will clean up gracefully.

## Project Structure

```
sherpa-ai/
├── src/
│   ├── capture/
│   │   ├── __init__.py
│   │   └── screen_capture.py         # Screenshot capture with mss
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── gemini_analyzer.py        # Gemini vision analysis
│   └── voice/
│       ├── __init__.py
│       └── sherpa_bot.py             # Pipecat voice bot
├── main.py                           # Main application loop
├── test_sherpa.py                    # Test suite
├── requirements.txt                  # Python dependencies
├── .env                              # API keys (not in git)
├── .gitignore                        # Git ignore rules
├── your-service-account.json         # Google Cloud creds (not in git)
└── README.md                         # This file
```

## Configuration

### Change Monitoring Interval

In `main.py`, line 19:

```python
self.capture = ScreenCapture(interval=120)  # Change to 2 minutes
```

### Adjust Intervention Sensitivity

In `src/analysis/gemini_analyzer.py`, line 116:

```python
def should_intervene(self) -> bool:
    return (
        self.last_analysis.get('needs_intervention', False) or
        self.distraction_count >= 3  # Trigger after 3 distractions instead of 1
    )
```

### Change VAD Sensitivity

In `src/voice/sherpa_bot.py`, line 44:

```python
vad_analyzer=SileroVADAnalyzer(
    params=VADParams(
        stop_secs=1.5,      # Wait longer for silence
        min_volume=0.7,     # Higher volume threshold
        confidence=0.8,     # More confidence required
    )
)
```

### Change TTS Voice

In `src/voice/sherpa_bot.py`, line 71:

```python
tts = GoogleTTSService(
    voice_id="en-US-Neural2-F",  # Different voice
    # Options: en-US-Journey-D, en-US-Studio-O, en-US-Wavenet-A, etc.
    params=GoogleTTSService.InputParams(language=Language.EN_US),
)
```

### Switch Gemini Model

In `src/voice/sherpa_bot.py`, line 67:

```python
llm = GoogleLLMService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-1.5-flash"  # Or use gemini-1.5-pro for better responses (slower, more expensive)
)
```

## Troubleshooting

### Screenshot Capture Issues

Problem: PermissionError or screenshots fail

- macOS: Grant screen recording permission in System Settings
- Linux: Ensure X11 or Wayland permissions are set
- Windows: Run as administrator if needed

### Gemini API Errors

Problem: 401 Unauthorized

- Verify GOOGLE_API_KEY in .env is correct
- Check key has permission at https://aistudio.google.com/

Problem: 429 Rate Limit Exceeded

- You've hit API quota (60 requests/min for gemini-1.5-flash)
- Wait a minute or upgrade your quota

### Google Cloud Authentication Errors

Problem: No valid credentials provided

- Check GOOGLE_APPLICATION_CREDENTIALS path in .env is correct
- Verify the JSON file exists and is readable
- Ensure Cloud Speech-to-Text and Text-to-Speech APIs are enabled
- Verify service account has correct roles

### Audio Issues

Problem: No audio from Sherpa

- Check system volume is up
- Verify speaker output device is correct
- Look for errors in terminal about audio devices

Problem: Sherpa keeps interrupting itself

- Solution: Use headphones! This prevents speaker output from feeding back into the microphone
- Alternative: Adjust VAD sensitivity higher

Problem: Sherpa doesn't hear you

- Check microphone permissions
- Test microphone with another app
- Increase microphone input volume

Problem: PyAudio installation fails

- macOS: Ensure brew install portaudio was run first
- Linux: Install portaudio19-dev package
- Windows: Try pip install pipwin && pipwin install pyaudio

### Pipeline/Pipecat Errors

Problem: LLMMessagesFrame is deprecated

- This is fixed in the current version - update your code

Problem: Voice conversation crashes

- Check all Google Cloud APIs are enabled
- Verify service account JSON has correct permissions
- Check API quotas aren't exceeded

## Privacy & Security

- Screenshots: Captured locally, sent to Gemini API for analysis, never stored
- Conversations: Processed through Google Cloud, not stored by Sherpa
- API Keys: Kept in .env file (excluded from git)
- Service Account: JSON credentials file (excluded from git)

## Rate Limits & Costs

Gemini API (Free Tier):

- Vision: 15 requests/minute, 1500/day
- LLM: 60 requests/minute (gemini-1.5-flash)

Google Cloud (Free Tier - First 12 months):

- Speech-to-Text: 60 minutes/month free
- Text-to-Speech: 1 million characters/month free

Typical Usage:

- Screen monitoring: ~1 request/minute (vision)
- Voice intervention: ~10-20 requests/conversation (LLM)
- TTS: ~100-200 characters/intervention

## Technical Details

Dependencies:

- pipecat-ai: Voice bot framework with pipeline architecture
- google-generativeai: Gemini vision and LLM
- google-cloud-speech: Speech-to-Text
- google-cloud-texttospeech: Text-to-Speech
- pyaudio: Local audio I/O
- mss: Fast screenshot capture
- python-dotenv: Environment variable management
- loguru: Better logging

Why These Choices?

Gemini 1.5 Flash:

- Fast vision analysis (< 1 second)
- High rate limits (60 req/min)
- Excellent context understanding
- Cost-effective

Local Audio (PyAudio):

- No browser dependency
- Lower latency
- Works offline (except API calls)
- Native system integration

Pipecat:

- Production-ready voice pipeline
- Supports multiple LLM/STT/TTS providers
- Built-in VAD and interruption handling
- Easy to extend

## Credits

Built for the AI Tinkerers Gemini Pipecat Hackathon

Technologies:

- Google Gemini - Vision & LLM
- Google Cloud Speech & TTS - Voice services
- Pipecat AI - Voice bot framework
- mss - Screenshot capture
- PyAudio - Audio I/O

## Support

For issues or questions:

- Open an issue on GitHub
- Check troubleshooting section above
- Review Google Cloud documentation for API issues
