#!/bin/bash
# Toggle Hand Mouse on/off.
# If running, kill it. If not running, start it.
#
# Usage:
#   ./toggle-hand-mouse.sh          (toggle)
#   Or add a shell alias:  alias hm='/path/to/toggle-hand-mouse.sh'

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.hand-mouse.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        osascript -e 'display notification "Hand Mouse stopped" with title "Hand Mouse"'
        echo "Hand Mouse stopped (PID $PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Start in background, redirect output to log
cd "$SCRIPT_DIR"
python3 main.py > "$SCRIPT_DIR/.hand-mouse.log" 2>&1 &
echo $! > "$PID_FILE"
osascript -e 'display notification "Hand Mouse started" with title "Hand Mouse"'
echo "Hand Mouse started (PID $!)"
