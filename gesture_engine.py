"""Gesture detection state machine.

States: IDLE, MOVING, LEFT_CLICK, RIGHT_CLICK, SCROLLING, SWIPING
"""

import math
import time
from enum import Enum, auto

import config
from hand_tracker import HandTracker


class Gesture(Enum):
    IDLE = auto()
    MOVING = auto()
    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    DRAGGING = auto()
    DRAG_END = auto()
    SCROLLING = auto()
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()


class GestureEngine:
    def __init__(self):
        self.state = Gesture.IDLE
        self.last_click_time = 0.0
        self.last_swipe_time = 0.0
        self.scroll_anchor_y = None
        self.prev_x = None
        self.prev_time = None
        self.dragging = False

    @staticmethod
    def _dist(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

    @staticmethod
    def _dist_2d(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def _is_finger_extended(self, lm, tip, pip):
        """Check if a finger is extended (tip is farther from wrist than PIP)."""
        wrist = lm[HandTracker.WRIST]
        return self._dist(lm[tip], wrist) > self._dist(lm[pip], wrist)

    def _fingers_extended(self, lm):
        """Return list of booleans for [index, middle, ring, pinky] extended."""
        return [
            self._is_finger_extended(lm, HandTracker.INDEX_TIP, HandTracker.INDEX_PIP),
            self._is_finger_extended(lm, HandTracker.MIDDLE_TIP, HandTracker.MIDDLE_PIP),
            self._is_finger_extended(lm, HandTracker.RING_TIP, HandTracker.RING_PIP),
            self._is_finger_extended(lm, HandTracker.PINKY_TIP, HandTracker.PINKY_PIP),
        ]

    def _is_thumb_extended(self, lm):
        return self._dist(lm[HandTracker.THUMB_TIP], lm[HandTracker.THUMB_MCP]) > \
               self._dist(lm[HandTracker.THUMB_IP], lm[HandTracker.THUMB_MCP])

    def update(self, landmarks):
        """Analyse landmarks (list of 21 NormalizedLandmark) and return (gesture, data_dict)."""
        now = time.time()
        lm = landmarks  # Already a list, index directly
        fingers = self._fingers_extended(lm)
        index_ext, middle_ext, ring_ext, pinky_ext = fingers
        thumb_ext = self._is_thumb_extended(lm)

        thumb_tip = lm[HandTracker.THUMB_TIP]
        index_tip = lm[HandTracker.INDEX_TIP]
        pinky_tip = lm[HandTracker.PINKY_TIP]
        middle_tip = lm[HandTracker.MIDDLE_TIP]

        # --- Drag: thumb-middle pinch (hold left mouse button) ---
        thumb_middle_dist = self._dist_2d(thumb_tip, middle_tip)

        if self.dragging:
            if thumb_middle_dist > config.DRAG_RELEASE_THRESHOLD:
                self.dragging = False
                self.state = Gesture.DRAG_END
                return Gesture.DRAG_END, {}
            else:
                self.state = Gesture.DRAGGING
                return Gesture.DRAGGING, {"x": index_tip.x, "y": index_tip.y}

        if thumb_middle_dist < config.DRAG_PINCH_THRESHOLD:
            self.dragging = True
            self.state = Gesture.DRAGGING
            self.scroll_anchor_y = None
            return Gesture.DRAGGING, {"x": index_tip.x, "y": index_tip.y}

        # --- Pinch detection (click) ---
        thumb_index_dist = self._dist_2d(thumb_tip, index_tip)
        thumb_pinky_dist = self._dist_2d(thumb_tip, pinky_tip)

        # Left click: thumb-index pinch
        if thumb_index_dist < config.PINCH_THRESHOLD:
            if now - self.last_click_time > config.CLICK_COOLDOWN:
                self.last_click_time = now
                self.state = Gesture.LEFT_CLICK
                self.scroll_anchor_y = None
                return Gesture.LEFT_CLICK, {}

        # Right click: thumb-pinky pinch
        if thumb_pinky_dist < config.PINCH_THRESHOLD:
            if now - self.last_click_time > config.CLICK_COOLDOWN:
                self.last_click_time = now
                self.state = Gesture.RIGHT_CLICK
                self.scroll_anchor_y = None
                return Gesture.RIGHT_CLICK, {}

        # --- Scroll: index + middle extended, others curled ---
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            avg_y = (index_tip.y + middle_tip.y) / 2.0
            if self.scroll_anchor_y is None:
                self.scroll_anchor_y = avg_y
                self.state = Gesture.SCROLLING
                return Gesture.SCROLLING, {"dy": 0}
            else:
                dy = (avg_y - self.scroll_anchor_y) * config.SCROLL_SPEED
                self.scroll_anchor_y = avg_y
                self.state = Gesture.SCROLLING
                return Gesture.SCROLLING, {"dy": dy}

        self.scroll_anchor_y = None

        # --- Swipe: all fingers extended (open hand), fast horizontal movement ---
        all_extended = index_ext and middle_ext and ring_ext and pinky_ext and thumb_ext
        if all_extended:
            wrist_x = lm[HandTracker.WRIST].x
            if self.prev_x is not None and self.prev_time is not None:
                dt = now - self.prev_time
                if dt > 0:
                    vx = (wrist_x - self.prev_x) / dt
                    if abs(vx) > config.SWIPE_VELOCITY_THRESHOLD and now - self.last_swipe_time > config.SWIPE_COOLDOWN:
                        self.last_swipe_time = now
                        self.prev_x = wrist_x
                        self.prev_time = now
                        if vx < 0:
                            self.state = Gesture.SWIPE_LEFT
                            return Gesture.SWIPE_LEFT, {}
                        else:
                            self.state = Gesture.SWIPE_RIGHT
                            return Gesture.SWIPE_RIGHT, {}
            self.prev_x = wrist_x
            self.prev_time = now
        else:
            self.prev_x = None
            self.prev_time = None

        # --- Move: index extended, others curled ---
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            self.state = Gesture.MOVING
            return Gesture.MOVING, {"x": index_tip.x, "y": index_tip.y}

        # --- Idle ---
        self.state = Gesture.IDLE
        return Gesture.IDLE, {}
