import cv2
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Global camera instance (stays open for better performance)
_camera = None
DEFAULT_CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))


def get_camera(camera_index=None):
    """Get or create the global camera instance"""
    global _camera
    if camera_index is None:
        camera_index = DEFAULT_CAMERA_INDEX
    if _camera is None or not _camera.isOpened():
        _camera = cv2.VideoCapture(camera_index)
        if _camera.isOpened():
            # Give camera time to initialize
            time.sleep(0.5)
            # Discard first few frames (often dark/blurry)
            for _ in range(5):
                _camera.read()
    return _camera


def capture_frame(camera_index=None):
    """
    Captures a single frame from the webcam.
    Returns JPEG image as bytes, or None if capture fails.

    If you get a black frame, try camera_index=1
    """
    if camera_index is None:
        camera_index = DEFAULT_CAMERA_INDEX
    cam = get_camera(camera_index)

    if not cam or not cam.isOpened():
        print(f"[Camera] Could not open camera at index {camera_index}")
        return None

    ret, frame = cam.read()

    if not ret or frame is None:
        print("[Camera] Failed to capture frame")
        return None

    # Encode frame to JPEG bytes at high quality
    success, buffer = cv2.imencode(
        '.jpg', frame,
        [cv2.IMWRITE_JPEG_QUALITY, 95]
    )

    if not success:
        print("[Camera] Failed to encode frame to JPEG")
        return None

    return buffer.tobytes()