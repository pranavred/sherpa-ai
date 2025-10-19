"""
Sherpa: AI Productivity Coach
Main application with screenshot monitoring + voice intervention.
"""
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

from src.capture.screen_capture import ScreenCapture
from src.analysis.gemini_analyzer import GeminiAnalyzer
from src.voice.sherpa_bot import start_voice_intervention

load_dotenv()

# Configuration
SCREENSHOT_INTERVAL_SECONDS = 10  # How often to take screenshots (in seconds)


class SherpaApp:
    def __init__(self, screenshot_interval: int = SCREENSHOT_INTERVAL_SECONDS):
        self.capture = ScreenCapture(interval=screenshot_interval)
        self.analyzer = GeminiAnalyzer(api_key=os.getenv('GOOGLE_API_KEY'))
        self.is_running = False
        self.in_conversation = False
        self.intervention_task = None

    async def voice_intervention(self):
        """Trigger voice intervention."""
        if self.in_conversation:
            return

        self.in_conversation = True

        try:
            context = self.analyzer.get_intervention_context()
            await start_voice_intervention(context, self.analyzer.current_task)

            # Reset distraction count after conversation
            self.analyzer.distraction_count = 0

        except Exception as e:
            logger.error(f"Voice intervention error: {e}")
        finally:
            self.in_conversation = False

    async def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("\n" + "="*60)
        logger.info("🏔️  SHERPA AI - Your Productivity Coach")
        logger.info("="*60)
        logger.info(f"📸 Taking screenshots every {self.capture.interval} seconds")
        logger.info(f"🎯 Current task: {self.analyzer.current_task}")
        logger.info("="*60 + "\n")

        self.is_running = True

        try:
            while self.is_running:
                # Capture screenshot
                img_bytes = self.capture.capture_screenshot()

                if img_bytes:
                    # Analyze with Gemini Vision
                    analysis = self.analyzer.analyze_screenshot(img_bytes)

                    # Check if intervention needed
                    if self.analyzer.should_intervene() and not self.in_conversation:
                        logger.warning("\n⚠️  INTERVENTION TRIGGERED!")
                        # Run intervention in a task so we can cancel it
                        self.intervention_task = asyncio.create_task(self.voice_intervention())

                # Wait for next interval
                await asyncio.sleep(self.capture.interval)

        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("\n\n👋 Sherpa shutting down...")
            self.is_running = False

            # Cancel any running intervention
            if self.intervention_task and not self.intervention_task.done():
                self.intervention_task.cancel()
                try:
                    await self.intervention_task
                except asyncio.CancelledError:
                    pass

    def set_task(self, task: str):
        """Set the current task."""
        self.analyzer.set_task(task)

    async def start(self, task: str = None):
        """Start Sherpa."""
        if task:
            self.set_task(task)

        await self.monitor_loop()


async def main():
    """Entry point."""
    # Check environment variables
    required_vars = ['GOOGLE_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        logger.info("Please set them in your .env file")
        return

    # Create and start Sherpa
    sherpa = SherpaApp()

    # Get task from user
    logger.info("🏔️  Welcome to Sherpa!\n")
    task = input("What are you working on today? ")

    if not task.strip():
        task = "general productivity"

    try:
        await sherpa.start(task)
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Exit cleanly
