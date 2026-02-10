"""Hand Mouse - Webcam hand tracking mouse controller.

Usage:
    python3 main.py

Controls:
    Ctrl+Shift+H  - Toggle hand tracking on/off
    Q (in debug window) - Quit
"""

import os
import threading
import time
import signal
from collections import deque

import cv2
import mediapipe as mp

import config
from hand_tracker import HandTracker
from gesture_engine import GestureEngine, Gesture
from mouse_controller import MouseController
from one_euro_filter import OneEuroFilter


class HandMouse:
    def __init__(self):
        self.active = True
        self.running = True
        self.tracker = HandTracker()
        self.gesture_engine = GestureEngine()
        self.mouse = MouseController()
        self.filter_x = OneEuroFilter(config.FILTER_MIN_CUTOFF, config.FILTER_BETA, config.FILTER_D_CUTOFF)
        self.filter_y = OneEuroFilter(config.FILTER_MIN_CUTOFF, config.FILTER_BETA, config.FILTER_D_CUTOFF)
        self.frame_queue = deque(maxlen=1)

    def _camera_loop(self, cap):
        """Read frames in a background thread."""
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            self.frame_queue.append(frame)

    def _map_to_screen(self, nx, ny):
        """Map normalised hand coordinates (with margin) to screen coordinates."""
        x = (nx - config.MARGIN_X) / (1.0 - 2 * config.MARGIN_X)
        y = (ny - config.MARGIN_Y) / (1.0 - 2 * config.MARGIN_Y)
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        return x * config.SCREEN_W, y * config.SCREEN_H

    def _draw_landmarks(self, frame, landmarks):
        """Draw hand skeleton on frame."""
        h, w, _ = frame.shape
        for connection in mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS:
            start = landmarks[connection.start]
            end = landmarks[connection.end]
            x1, y1 = int(start.x * w), int(start.y * h)
            x2, y2 = int(end.x * w), int(end.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

    def _start_hotkey_listener(self):
        """Start pynput keyboard listener for Ctrl+Shift+H toggle."""
        from pynput import keyboard

        pressed = set()

        def on_press(key):
            try:
                k = key.char.lower() if hasattr(key, "char") and key.char else None
            except AttributeError:
                k = None

            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                pressed.add("ctrl")
            elif key == keyboard.Key.shift or key == keyboard.Key.shift_r:
                pressed.add("shift")
            elif k:
                pressed.add(k)

            if config.HOTKEY_MODIFIERS.issubset(pressed) and config.HOTKEY_KEY in pressed:
                self.active = not self.active
                state = "ON" if self.active else "OFF"
                print(f"Hand Mouse: {state}")
                if self.active:
                    self.filter_x.reset()
                    self.filter_y.reset()

        def on_release(key):
            try:
                k = key.char.lower() if hasattr(key, "char") and key.char else None
            except AttributeError:
                k = None

            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                pressed.discard("ctrl")
            elif key == keyboard.Key.shift or key == keyboard.Key.shift_r:
                pressed.discard("shift")
            elif k:
                pressed.discard(k)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()

    def run(self):
        print("Hand Mouse starting...")
        print(f"Screen: {config.SCREEN_W}x{config.SCREEN_H}")
        print("Press Ctrl+Shift+H to toggle tracking")
        print("Press Q in debug window to quit")

        # Open camera on main thread (required for macOS camera authorization)
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_H)

        if not cap.isOpened():
            print("ERROR: Cannot open camera.")
            print("Grant camera access: System Settings > Privacy & Security > Camera")
            return

        print("Camera opened successfully.")

        # Start frame reading in background thread
        cam_thread = threading.Thread(target=self._camera_loop, args=(cap,), daemon=True)
        cam_thread.start()

        # Start hotkey listener
        self._start_hotkey_listener()

        # Handle Ctrl+C
        signal.signal(signal.SIGINT, lambda *_: setattr(self, "running", False))

        while self.running:
            if not self.frame_queue:
                time.sleep(0.001)
                continue

            frame = self.frame_queue.pop()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = self.tracker.process(frame_rgb)

            if landmarks and self.active:
                gesture, data = self.gesture_engine.update(landmarks)
                now = time.time()

                if gesture == Gesture.MOVING:
                    sx, sy = self._map_to_screen(data["x"], data["y"])
                    sx = self.filter_x(sx, now)
                    sy = self.filter_y(sy, now)
                    self.mouse.move(sx, sy)

                elif gesture == Gesture.DRAGGING:
                    sx, sy = self._map_to_screen(data["x"], data["y"])
                    sx = self.filter_x(sx, now)
                    sy = self.filter_y(sy, now)
                    self.mouse.drag_move(sx, sy)

                elif gesture == Gesture.DRAG_END:
                    self.mouse.drag_end()

                elif gesture == Gesture.LEFT_CLICK:
                    self.mouse.left_click()

                elif gesture == Gesture.RIGHT_CLICK:
                    self.mouse.right_click()

                elif gesture == Gesture.SCROLLING:
                    if data["dy"] != 0:
                        self.mouse.scroll(data["dy"])

                elif gesture == Gesture.SWIPE_LEFT:
                    self.mouse.swipe_back()

                elif gesture == Gesture.SWIPE_RIGHT:
                    self.mouse.swipe_forward()

            # Debug overlay
            if config.DEBUG_WINDOW:
                if landmarks:
                    self._draw_landmarks(frame, landmarks)
                    state_text = self.gesture_engine.state.name
                else:
                    state_text = "NO HAND"

                status = "ACTIVE" if self.active else "PAUSED"
                cv2.putText(frame, f"{status} | {state_text}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow(config.DEBUG_WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        self.running = False
        cap.release()
        self.tracker.close()
        cv2.destroyAllWindows()
        print("Hand Mouse stopped.")


if __name__ == "__main__":
    HandMouse().run()
