#!/bin/bash
# Toggle Hand Mouse on/off.
# If running, kill it. If not running, start it.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.hand-mouse.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        osascript -e 'display notification "Hand Mouse stopped" with title "Hand Mouse"'
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Start in background
cd "$SCRIPT_DIR"
python3 main.py &
echo $! > "$PID_FILE"
osascript -e 'display notification "Hand Mouse started" with title "Hand Mouse"'
