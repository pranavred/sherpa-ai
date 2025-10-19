"""
Sherpa voice bot using Google STT + Gemini LLM + Google TTS.
Runs locally using your laptop's microphone and speakers (no browser required).
"""
import asyncio
import os
from datetime import datetime

from loguru import logger
from dotenv import load_dotenv

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame, TextFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.google.tts import GoogleTTSService
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.frames.frames import TranscriptionFrame

load_dotenv()


class GoodbyeDetector(FrameProcessor):
    """Detects when Sherpa says GOODBYE and ends the conversation."""

    def __init__(self):
        super().__init__()
        self._should_end = False
        self._goodbye_detected = False

    async def process_frame(self, frame, direction):
        """Check if the text contains GOODBYE."""
        await super().process_frame(frame, direction)

        # Pass the frame along first
        await self.push_frame(frame, direction)

        # Check text frames from the LLM for GOODBYE
        # Only check once to avoid multiple EndFrames
        if isinstance(frame, TextFrame) and not self._goodbye_detected:
            if "GOODBYE" in frame.text.upper():
                logger.info("👋 Sherpa said goodbye - will end conversation after audio finishes")
                self._goodbye_detected = True
                # Queue an EndFrame to stop the pipeline AFTER this text is spoken
                await self.push_frame(EndFrame())


async def run_sherpa_bot(
    intervention_context: str,
    current_task: str
):
    """
    Run Sherpa voice bot using Google cascade (STT -> LLM -> TTS).
    Uses local audio (microphone + speakers) - no browser required.
    """

    # Local audio transport - uses your laptop's microphone and speakers
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=1.0,        # Wait 1 second of silence before considering speech done
                    min_volume=0.6,       # Increase minimum volume threshold (0-1, default 0.5)
                    confidence=0.7,       # Increase confidence threshold (0-1, default 0.5)
                )
            ),
        )
    )

    try:

        # Get credentials path from environment
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        # Google Speech-to-Text
        stt = GoogleSTTService(
            params=GoogleSTTService.InputParams(language=Language.EN_US),
            credentials_path=credentials_path,
        )

        # Google Gemini LLM
        llm = GoogleLLMService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.0-flash-exp"
        )

        # Google Text-to-Speech
        tts = GoogleTTSService(
            voice_id="en-US-Journey-D",  # Natural, warm voice
            params=GoogleTTSService.InputParams(language=Language.EN_US),
            credentials_path=credentials_path,
        )

        # System prompt for Sherpa
        system_prompt = f"""You are Sherpa, a warm and supportive productivity coach speaking via voice.

{intervention_context}

Your personality:
- Speak conversationally and naturally (use contractions, casual language)
- Be genuinely curious, not accusatory or judgmental
- Keep responses SHORT (1-2 sentences max) - this is a voice conversation
- Use the person's responses to help them reflect
- Acknowledge when they have good reasons for what they're doing
- Suggest getting back on track gently if appropriate
- Be encouraging and supportive

Example approaches:
- "Hey! I noticed you're on [activity]. What's up with that?"
- "Interesting - how does [activity] connect to [task]?"
- "Taking a quick break? That's totally fine!"
- "I hear you. Want to get back to [task], or is there something blocking you?"

IMPORTANT - Ending the conversation:
When the user indicates they want to get back to work (e.g., "let me get back to it", "I'll focus now", "yeah I should work"), respond with a brief encouraging message and then say "GOODBYE" to end the conversation.

Example endings:
- "Great! Good luck with your coding. GOODBYE"
- "Sounds good! I'll check in later if needed. GOODBYE"
- "Perfect! Get back to it. GOODBYE"

Remember: Keep it SHORT. Voice conversations should feel natural, not like reading an essay.

Start by saying: "Hey! I noticed you might be off track. What are you working on right now?"
"""

        # Create LLM context with system message and initial user trigger
        # The user message triggers Sherpa to speak first (required for LLM to respond)
        initial_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Hi Sherpa"},  # Triggers the initial greeting
        ]

        context = LLMContext(messages=initial_messages)
        context_aggregator = LLMContextAggregatorPair(context)

        # Create goodbye detector
        goodbye_detector = GoodbyeDetector()

        # Pipeline: Input -> STT -> User Context -> LLM -> Goodbye Detector -> TTS -> Output -> Assistant Context
        pipeline = Pipeline([
            transport.input(),              # Audio in from microphone
            stt,                            # Google Speech-to-Text
            context_aggregator.user(),      # Add user messages to context
            llm,                            # Gemini LLM
            goodbye_detector,               # Detect GOODBYE and end conversation
            tts,                            # Google Text-to-Speech
            transport.output(),             # Audio out to speakers
            context_aggregator.assistant(), # Add assistant messages to context
        ])

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            )
        )

        # Run the pipeline
        runner = PipelineRunner()

        logger.info("🎤 Sherpa voice bot starting...")
        logger.info("🎧 Listening through your microphone...")
        logger.info("🔊 Speaking through your speakers...")
        logger.info("💬 Sherpa will speak first...\n")

        # Create an async task to queue the initial greeting after pipeline starts
        async def queue_initial_greeting():
            # Wait a bit for pipeline to be fully ready
            await asyncio.sleep(0.5)
            # Queue initial transcription to trigger Sherpa's greeting
            await task.queue_frames([
                TranscriptionFrame(text="Hi Sherpa", user_id="user", timestamp=datetime.now().isoformat())
            ])

        # Start the greeting task
        greeting_task = asyncio.create_task(queue_initial_greeting())

        # Run the bot - Sherpa will speak first with the greeting
        await runner.run(task)

        # Cleanup
        if not greeting_task.done():
            greeting_task.cancel()

        logger.info("\n👋 Sherpa voice bot ended")

    except KeyboardInterrupt:
        logger.info("\n👋 Conversation ended by user")
    except Exception as e:
        logger.error(f"Error in voice bot: {e}")
        raise


async def start_voice_intervention(intervention_context: str, current_task: str):
    """Start a voice intervention conversation using local audio."""
    logger.info(f"\n🎤 SHERPA SPEAKING!")
    logger.info(f"   Using your laptop's microphone and speakers\n")

    await run_sherpa_bot(intervention_context, current_task)
