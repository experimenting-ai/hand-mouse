"""macOS mouse control via Quartz CGEvent API."""

import Quartz
from Quartz import (
    CGEventCreateMouseEvent,
    CGEventCreateScrollWheelEvent,
    CGEventPost,
    CGEventSetIntegerValueField,
    kCGEventMouseMoved,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGHIDEventTap,
    kCGMouseButtonLeft,
    kCGMouseButtonRight,
    kCGScrollEventUnitPixel,
)
import subprocess


class MouseController:
    def __init__(self):
        self._last_pos = (0, 0)
        self._dragging = False

    def move(self, x, y):
        """Move the mouse cursor to absolute screen coordinates."""
        point = Quartz.CGPoint(x, y)
        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, point, kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        self._last_pos = (x, y)

    def left_click(self):
        """Perform a left click at current position."""
        point = Quartz.CGPoint(*self._last_pos)
        down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
        up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)

    def right_click(self):
        """Perform a right click at current position."""
        point = Quartz.CGPoint(*self._last_pos)
        down = CGEventCreateMouseEvent(None, kCGEventRightMouseDown, point, kCGMouseButtonRight)
        up = CGEventCreateMouseEvent(None, kCGEventRightMouseUp, point, kCGMouseButtonRight)
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)

    def drag_move(self, x, y):
        """Move while holding left mouse button (drag)."""
        point = Quartz.CGPoint(x, y)
        if not self._dragging:
            # Press down to start drag
            down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, down)
            self._dragging = True
        else:
            # Continue dragging
            from Quartz import kCGEventLeftMouseDragged
            drag = CGEventCreateMouseEvent(None, kCGEventLeftMouseDragged, point, kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, drag)
        self._last_pos = (x, y)

    def drag_end(self):
        """Release left mouse button to end drag."""
        if self._dragging:
            point = Quartz.CGPoint(*self._last_pos)
            up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, up)
            self._dragging = False

    def scroll(self, dy):
        """Scroll vertically. Positive dy = scroll down, negative = scroll up."""
        # CGEvent scroll: positive = scroll up in Quartz, so we invert
        units = int(-dy * 10)
        if units == 0:
            return
        event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitPixel, 1, units)
        CGEventPost(kCGHIDEventTap, event)

    def swipe_back(self):
        """Simulate browser back (Cmd+[)."""
        subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to keystroke "[" using command down'],
            capture_output=True,
        )

    def swipe_forward(self):
        """Simulate browser forward (Cmd+])."""
        subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to keystroke "]" using command down'],
            capture_output=True,
        )
