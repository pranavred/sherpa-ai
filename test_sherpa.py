"""Quick test to verify everything works."""
import asyncio
import os
from dotenv import load_dotenv
from src.capture.screen_capture import ScreenCapture
from src.analysis.gemini_analyzer import GeminiAnalyzer

load_dotenv()

async def test_capture_and_analysis():
    """Test screenshot capture and Gemini analysis."""
    print("🧪 Testing Sherpa components...\n")

    # Test 1: Screenshot capture
    print("Test 1: Screenshot Capture")
    capture = ScreenCapture(interval=10)
    img_bytes = capture.capture_screenshot()

    if img_bytes:
        print(f"✅ Screenshot captured ({len(img_bytes)} bytes)\n")
    else:
        print("❌ Screenshot capture failed\n")
        return

    # Test 2: Gemini vision analysis
    print("Test 2: Gemini Vision Analysis")
    analyzer = GeminiAnalyzer(api_key=os.getenv('GOOGLE_API_KEY'))
    analyzer.set_task("Writing Python code for an AI agent")

    analysis = analyzer.analyze_screenshot(img_bytes)

    print(f"\n✅ Analysis complete:")
    print(f"   Activity: {analysis['activity_detected']}")
    print(f"   On-task: {analysis['is_on_task']}")
    print(f"   Should intervene: {analyzer.should_intervene()}\n")

    # Test 3: Multiple captures with intervention check
    print("Test 3: Multiple Captures (simulating distractions)")
    print("   Switch to different apps between captures to test detection\n")

    for i in range(3):
        print(f"Capture {i+1}/3...")
        img_bytes = capture.capture_screenshot()

        if img_bytes:
            analysis = analyzer.analyze_screenshot(img_bytes)

            if analyzer.should_intervene():
                print("\n🚨 WOULD TRIGGER VOICE INTERVENTION HERE!")
                print(f"Context: {analyzer.get_intervention_context()}\n")
                break

        if i < 2:
            print(f"Waiting 10 seconds... (switch apps now)\n")
            await asyncio.sleep(10)

    print("✅ All tests complete!")

if __name__ == "__main__":
    asyncio.run(test_capture_and_analysis())
