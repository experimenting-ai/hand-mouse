# Hand Mouse - Webcam Hand Tracking Mouse Controller

## Overview
A Python app that uses your webcam + MediaPipe hand tracking to control the mouse cursor with hand gestures. Designed for macOS.

## Tech Stack
- **MediaPipe** - Hand landmark detection (21 3D landmarks per hand)
- **OpenCV** - Webcam capture and debug overlay window
- **Quartz (CoreGraphics)** - Native macOS mouse control (~1-5ms latency vs ~100ms with PyAutoGUI)
- **pynput** - Keyboard listener for toggle hotkey
- **One Euro Filter** - Adaptive smoothing to eliminate jitter while keeping low latency

## Gesture Mappings
| Action | Gesture |
|--------|---------|
| **Move cursor** | Index finger extended, other fingers curled |
| **Left click** | Thumb tip pinches Index finger tip |
| **Right click** | Thumb tip pinches Pinky finger tip |
| **Scroll up/down** | Index + Middle fingers extended, move hand up/down |
| **Swipe left (back)** | Open hand swipe left |
| **Swipe right (forward)** | Open hand swipe right |
| **Toggle on/off** | Ctrl+Shift+H hotkey |

## Architecture
```
Camera Thread  -->  Frame Queue (latest only)  -->  Main Processing Loop
                                                      |
                                                      +-- MediaPipe inference
                                                      +-- Gesture state machine
                                                      +-- One Euro Filter smoothing
                                                      +-- Coordinate mapping to screen
                                                      +-- Quartz CGEvent mouse actions
                                                      +-- Debug overlay (cv2.imshow)
```

## Files to Create
```
hand-mouse/
├── requirements.txt          # Dependencies
├── main.py                   # Entry point + main loop
├── hand_tracker.py           # MediaPipe wrapper, landmark extraction
├── gesture_engine.py         # Gesture detection state machine
├── mouse_controller.py       # Quartz-based mouse control (move, click, scroll, swipe)
├── one_euro_filter.py        # Jitter smoothing filter
├── config.py                 # All tunable constants (thresholds, sensitivity, etc.)
└── PLAN.md                   # This file
```

## Implementation Steps

### Step 1: `config.py` - Configuration constants
All thresholds, sensitivity values, screen margins, hotkey binding in one place.

### Step 2: `one_euro_filter.py` - Smoothing filter
Implements the One Euro Filter algorithm for adaptive jitter reduction.

### Step 3: `hand_tracker.py` - Hand tracking wrapper
Wraps MediaPipe Hands, returns structured landmark data per frame.

### Step 4: `gesture_engine.py` - Gesture state machine
Detects gestures from landmarks: IDLE, MOVING, LEFT_CLICK, RIGHT_CLICK, SCROLLING, SWIPING.
Includes debouncing, cooldowns, and velocity-based swipe detection.

### Step 5: `mouse_controller.py` - macOS mouse control
Uses Quartz CGEvent API for: move, left click, right click, scroll, swipe (Cmd+[ / Cmd+]).

### Step 6: `main.py` - Entry point
- Camera capture in separate thread
- Main processing loop
- Debug window with hand skeleton overlay
- Ctrl+Shift+H toggle via pynput keyboard listener
- Graceful shutdown

### Step 7: `requirements.txt` + testing
Install, test, iterate on thresholds.

## macOS Permissions Required
1. **Camera** - System Settings > Privacy & Security > Camera > Terminal/iTerm
2. **Accessibility** - System Settings > Privacy & Security > Accessibility > Terminal/iTerm
3. **Input Monitoring** - System Settings > Privacy & Security > Input Monitoring > Terminal/iTerm (for hotkey)
