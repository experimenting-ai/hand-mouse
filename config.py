"""Configuration constants for hand-mouse."""

import Quartz

# --- Screen ---
SCREEN_W = Quartz.CGDisplayPixelsWide(Quartz.CGMainDisplayID())
SCREEN_H = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())

# --- Camera ---
CAMERA_INDEX = 0
CAMERA_W = 640
CAMERA_H = 480

# --- MediaPipe ---
MP_MAX_HANDS = 1
MP_DETECTION_CONFIDENCE = 0.7
MP_TRACKING_CONFIDENCE = 0.7

# --- Coordinate mapping ---
# Margins (fraction of frame) to avoid requiring hand at very edges
MARGIN_X = 0.1
MARGIN_Y = 0.1

# --- One Euro Filter ---
FILTER_MIN_CUTOFF = 1.0   # Lower = more smoothing at low speed
FILTER_BETA = 0.007        # Higher = less lag at high speed
FILTER_D_CUTOFF = 1.0      # Derivative cutoff frequency

# --- Gesture thresholds ---
PINCH_THRESHOLD = 0.045       # Normalised distance for pinch detection
PINCH_RELEASE_THRESHOLD = 0.06
FINGER_CURL_THRESHOLD = 0.15  # MCP-to-tip distance ratio for "curled"
SCROLL_SPEED = 5              # Scroll units per frame of movement
SWIPE_VELOCITY_THRESHOLD = 1.2  # Normalised units/sec for swipe trigger
SWIPE_COOLDOWN = 0.5          # Seconds between swipes
CLICK_COOLDOWN = 0.25         # Seconds between clicks
DRAG_PINCH_THRESHOLD = 0.045  # Thumb-middle pinch to start drag
DRAG_RELEASE_THRESHOLD = 0.07 # Release drag when distance exceeds this

# --- Hotkey ---
HOTKEY_MODIFIERS = {"ctrl", "shift"}
HOTKEY_KEY = "h"

# --- Debug window ---
DEBUG_WINDOW = True
DEBUG_WINDOW_NAME = "Hand Mouse Debug"
