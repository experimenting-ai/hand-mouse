"""MediaPipe hand tracking wrapper (tasks API)."""

import os
import mediapipe as mp
import config

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")


class HandTracker:
    # Landmark indices (MediaPipe convention)
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    def __init__(self):
        base_options = mp.tasks.BaseOptions(model_asset_path=_MODEL_PATH)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=config.MP_MAX_HANDS,
            min_hand_detection_confidence=config.MP_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MP_TRACKING_CONFIDENCE,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self._frame_ts = 0

    def process(self, frame_rgb):
        """Process an RGB frame. Returns list of 21 NormalizedLandmark or None."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        self._frame_ts += 1
        result = self.landmarker.detect_for_video(mp_image, self._frame_ts)
        if result.hand_landmarks:
            return result.hand_landmarks[0]  # List of 21 NormalizedLandmark
        return None

    def close(self):
        self.landmarker.close()
