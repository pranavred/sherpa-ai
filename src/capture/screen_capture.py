"""Screenshot capture for Sherpa."""
import mss
from PIL import Image
import io
from typing import Optional
import time

class ScreenCapture:
    def __init__(self, interval: int = 60):
        """
        Initialize screen capture.

        Args:
            interval: Seconds between captures (default 60)
        """
        self.interval = interval
        self.sct = mss.mss()
        self.last_capture_time = 0

    def capture_screenshot(self) -> Optional[bytes]:
        """Capture current screen as PNG bytes."""
        try:
            monitor = self.sct.monitors[1]  # Primary monitor
            screenshot = self.sct.grab(monitor)

            img = Image.frombytes(
                'RGB',
                (screenshot.width, screenshot.height),
                screenshot.rgb
            )

            # Resize for API efficiency (max 1280px wide)
            if img.width > 1280:
                ratio = 1280 / img.width
                new_size = (1280, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to PNG bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            self.last_capture_time = time.time()
            return img_byte_arr.getvalue()

        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            return None

    def should_capture(self) -> bool:
        """Check if enough time has passed since last capture."""
        return (time.time() - self.last_capture_time) >= self.interval
