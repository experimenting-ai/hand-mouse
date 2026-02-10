"""Gesture detection state machine.

States: IDLE, MOVING, LEFT_CLICK, RIGHT_CLICK, DRAGGING, DRAG_END, SCROLLING, SWIPING
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
        self.scroll_momentum = 0.0
        self.prev_x = None
        self.prev_time = None
        self.swipe_start_x = None  # Track start position for min distance
        self.dragging = False
        # Click hysteresis: track whether pinch was released since last click
        self.left_click_armed = True
        self.right_click_armed = True
        # Debug info (updated each frame)
        self.debug = {
            "thumb_cross": 0.0,
            "thumb_middle": 0.0,
            "thumb_pinky": 0.0,
            "fingers": [False, False, False, False],
            "scroll_dy": 0.0,
        }

    def reset(self):
        """Reset all gesture state (call on toggle/disconnect)."""
        self.state = Gesture.IDLE
        self.scroll_anchor_y = None
        self.scroll_momentum = 0.0
        self.prev_x = None
        self.prev_time = None
        self.swipe_start_x = None
        self.dragging = False
        self.left_click_armed = True
        self.right_click_armed = True

    @staticmethod
    def _dist(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

    @staticmethod
    def _dist_2d(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def _is_finger_extended(self, lm, tip, pip):
        wrist = lm[HandTracker.WRIST]
        return self._dist(lm[tip], wrist) > self._dist(lm[pip], wrist)

    def _fingers_extended(self, lm):
        return [
            self._is_finger_extended(lm, HandTracker.INDEX_TIP, HandTracker.INDEX_PIP),
            self._is_finger_extended(lm, HandTracker.MIDDLE_TIP, HandTracker.MIDDLE_PIP),
            self._is_finger_extended(lm, HandTracker.RING_TIP, HandTracker.RING_PIP),
            self._is_finger_extended(lm, HandTracker.PINKY_TIP, HandTracker.PINKY_PIP),
        ]

    def _is_thumb_extended(self, lm):
        return self._dist(lm[HandTracker.THUMB_TIP], lm[HandTracker.THUMB_MCP]) > \
               self._dist(lm[HandTracker.THUMB_IP], lm[HandTracker.THUMB_MCP])

    def update_momentum(self):
        """Tick momentum scrolling (call every frame, even without hand)."""
        if abs(self.scroll_momentum) > config.SCROLL_MOMENTUM_MIN:
            self.scroll_momentum *= config.SCROLL_MOMENTUM_DECAY
            return self.scroll_momentum
        self.scroll_momentum = 0.0
        return 0.0

    def update(self, landmarks):
        """Analyse landmarks and return (gesture, data_dict)."""
        now = time.time()
        lm = landmarks

        # Validate landmark data (NaN guard)
        try:
            _ = lm[0].x + lm[0].y
        except (TypeError, AttributeError):
            self.state = Gesture.IDLE
            return Gesture.IDLE, {}

        fingers = self._fingers_extended(lm)
        index_ext, middle_ext, ring_ext, pinky_ext = fingers
        thumb_ext = self._is_thumb_extended(lm)

        thumb_tip = lm[HandTracker.THUMB_TIP]
        index_tip = lm[HandTracker.INDEX_TIP]
        pinky_tip = lm[HandTracker.PINKY_TIP]
        middle_tip = lm[HandTracker.MIDDLE_TIP]

        # Compute distances once
        thumb_middle_dist = self._dist_2d(thumb_tip, middle_tip)
        thumb_pinky_dist = self._dist_2d(thumb_tip, pinky_tip)

        # Left click: thumb cross under palm (thumb tip crosses past index MCP on x-axis)
        index_mcp = lm[HandTracker.INDEX_MCP]
        # Thumb crosses when its tip goes past index MCP toward pinky side
        # In mirrored camera view: thumb tip x > index MCP x means crossed
        thumb_cross = thumb_tip.x - index_mcp.x

        # Update debug info
        self.debug["thumb_cross"] = thumb_cross
        self.debug["thumb_middle"] = thumb_middle_dist
        self.debug["thumb_pinky"] = thumb_pinky_dist
        self.debug["fingers"] = fingers

        # --- Drag: thumb-middle pinch (hold left mouse button) ---
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
            self.scroll_momentum = 0.0
            return Gesture.DRAGGING, {"x": index_tip.x, "y": index_tip.y}

        # --- Left click: thumb cross under index finger ---
        if thumb_cross > config.THUMB_CROSS_THRESHOLD:
            if self.left_click_armed and now - self.last_click_time > config.CLICK_COOLDOWN:
                self.last_click_time = now
                self.left_click_armed = False
                self.state = Gesture.LEFT_CLICK
                self.scroll_anchor_y = None
                self.scroll_momentum = 0.0
                return Gesture.LEFT_CLICK, {}
        elif thumb_cross < -config.THUMB_CROSS_RELEASE:
            self.left_click_armed = True

        # --- Right click: thumb-pinky pinch ---
        if thumb_pinky_dist < config.PINCH_THRESHOLD:
            if self.right_click_armed and now - self.last_click_time > config.CLICK_COOLDOWN:
                self.last_click_time = now
                self.right_click_armed = False
                self.state = Gesture.RIGHT_CLICK
                self.scroll_anchor_y = None
                self.scroll_momentum = 0.0
                return Gesture.RIGHT_CLICK, {}
        elif thumb_pinky_dist > config.PINCH_RELEASE_THRESHOLD:
            self.right_click_armed = True

        # --- Scroll: index + middle extended, others curled ---
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            avg_y = (index_tip.y + middle_tip.y) / 2.0
            if self.scroll_anchor_y is None:
                self.scroll_anchor_y = avg_y
                self.state = Gesture.SCROLLING
                return Gesture.SCROLLING, {"dy": 0}
            else:
                dy = (avg_y - self.scroll_anchor_y) * config.SCROLL_SPEED
                # Use a moving anchor (smoothed) instead of resetting every frame
                self.scroll_anchor_y = 0.7 * self.scroll_anchor_y + 0.3 * avg_y
                self.scroll_momentum = dy  # Feed momentum
                self.debug["scroll_dy"] = dy
                self.state = Gesture.SCROLLING
                return Gesture.SCROLLING, {"dy": dy}

        # Don't reset scroll anchor immediately - only after leaving scroll pose
        # for a few frames (handled by the fact that momentum continues)
        if self.state == Gesture.SCROLLING:
            self.scroll_anchor_y = None

        # --- Swipe: all fingers extended, fast horizontal + minimum distance ---
        all_extended = index_ext and middle_ext and ring_ext and pinky_ext and thumb_ext
        if all_extended:
            wrist_x = lm[HandTracker.WRIST].x
            if self.prev_x is not None and self.prev_time is not None:
                dt = now - self.prev_time
                if dt > 0.005:  # Ignore tiny dt to avoid velocity spikes
                    vx = (wrist_x - self.prev_x) / dt
                    # Check minimum travel distance from swipe start
                    travel = abs(wrist_x - self.swipe_start_x) if self.swipe_start_x is not None else 0
                    if (abs(vx) > config.SWIPE_VELOCITY_THRESHOLD
                            and travel > config.SWIPE_MIN_DISTANCE
                            and now - self.last_swipe_time > config.SWIPE_COOLDOWN):
                        self.last_swipe_time = now
                        self.prev_x = wrist_x
                        self.prev_time = now
                        self.swipe_start_x = wrist_x  # Reset start for next swipe
                        if vx < 0:
                            self.state = Gesture.SWIPE_LEFT
                            return Gesture.SWIPE_LEFT, {}
                        else:
                            self.state = Gesture.SWIPE_RIGHT
                            return Gesture.SWIPE_RIGHT, {}
            else:
                self.swipe_start_x = wrist_x  # Mark swipe start position
            self.prev_x = wrist_x
            self.prev_time = now
        else:
            self.prev_x = None
            self.prev_time = None
            self.swipe_start_x = None

        # --- Move: index extended, others curled ---
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            self.state = Gesture.MOVING
            return Gesture.MOVING, {"x": index_tip.x, "y": index_tip.y}

        # --- Idle ---
        self.state = Gesture.IDLE
        return Gesture.IDLE, {}
