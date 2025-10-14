"""
Sherpa voice bot using Google STT + Gemini LLM + Google TTS.
Runs locally using your laptop's microphone and speakers (no browser required).
"""
import asyncio
import os

from loguru import logger
from dotenv import load_dotenv

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.google.tts import GoogleTTSService
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

load_dotenv()


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
            model="gemini-1.5-flash"
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

Remember: Keep it SHORT. Voice conversations should feel natural, not like reading an essay.

Start by saying: "Hey! I noticed you might be off track. What are you working on right now?"
"""

        # Create LLM context with system message
        initial_messages = [
            {"role": "system", "content": system_prompt},
        ]

        context = LLMContext(messages=initial_messages)
        context_aggregator = LLMContextAggregatorPair(context)

        # Pipeline: Input -> STT -> User Context -> LLM -> TTS -> Output -> Assistant Context
        pipeline = Pipeline([
            transport.input(),              # Audio in from microphone
            stt,                            # Google Speech-to-Text
            context_aggregator.user(),      # Add user messages to context
            llm,                            # Gemini LLM
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
        logger.info("💬 Say something or press Ctrl+C to end\n")

        # Run the bot - it will start automatically with the context
        await runner.run(task)

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
