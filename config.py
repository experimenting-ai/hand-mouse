"""Configuration constants for hand-mouse."""

import Quartz

# --- Screen ---
SCREEN_W = Quartz.CGDisplayPixelsWide(Quartz.CGMainDisplayID())
SCREEN_H = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())

# --- Camera ---
CAMERA_INDEX = 0
CAMERA_W = 640
CAMERA_H = 480
CAMERA_FAIL_LIMIT = 30  # Consecutive failed reads before declaring disconnect

# --- MediaPipe ---
MP_MAX_HANDS = 1
MP_DETECTION_CONFIDENCE = 0.7
MP_TRACKING_CONFIDENCE = 0.7

# --- Coordinate mapping ---
MARGIN_X = 0.1
MARGIN_Y = 0.1

# --- One Euro Filter ---
FILTER_MIN_CUTOFF = 1.0
FILTER_BETA = 0.007
FILTER_D_CUTOFF = 1.0

# --- Gesture thresholds ---
# Left click: thumb crosses under index finger (thumb tip past index MCP)
THUMB_CROSS_THRESHOLD = 0.02   # Thumb tip must be this far past index MCP (x-axis)
THUMB_CROSS_RELEASE = 0.01     # Hysteresis release margin
# Right click: thumb-pinky pinch
PINCH_THRESHOLD = 0.045
PINCH_RELEASE_THRESHOLD = 0.06
FINGER_CURL_THRESHOLD = 0.15
SCROLL_SPEED = 5
SWIPE_VELOCITY_THRESHOLD = 1.2
SWIPE_MIN_DISTANCE = 0.08      # Minimum wrist travel before swipe can fire
SWIPE_COOLDOWN = 0.5
CLICK_COOLDOWN = 0.15           # Reduced for double-click support
DRAG_PINCH_THRESHOLD = 0.045
DRAG_RELEASE_THRESHOLD = 0.07

# --- Momentum scrolling ---
SCROLL_MOMENTUM_DECAY = 0.85   # Multiply momentum by this each frame
SCROLL_MOMENTUM_MIN = 0.01     # Stop when momentum drops below this

# --- Hotkey ---
HOTKEY_MODIFIERS = {"ctrl", "shift"}
HOTKEY_KEY = "h"

# --- Debug window ---
DEBUG_WINDOW = True
DEBUG_WINDOW_NAME = "Hand Mouse Debug"
