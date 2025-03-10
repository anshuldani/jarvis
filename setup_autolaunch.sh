#!/bin/bash
# J.A.R.V.I.S. macOS Auto-Launch Setup
# Makes JARVIS start automatically when you log in

JARVIS_DIR="$(cd "$(dirname "$0")" && pwd)"
CONDA_BASE="$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")"
PLIST="$HOME/Library/LaunchAgents/com.jarvis.assistant.plist"
LAUNCHER="$HOME/jarvis_launch.sh"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  J.A.R.V.I.S. Auto-Launch Setup             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  JARVIS directory : $JARVIS_DIR"
echo "  Conda base       : $CONDA_BASE"
echo ""

# Get API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f "$JARVIS_DIR/.env" ]; then
        source "$JARVIS_DIR/.env"
    fi
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "  ⚠  ANTHROPIC_API_KEY not set."
    echo "     Add it to $JARVIS_DIR/.env first, then re-run this script."
    exit 1
fi

# Create launcher script
cat > "$LAUNCHER" << SCRIPT
#!/bin/bash
source "$CONDA_BASE/bin/activate" base
export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
export ELEVENLABS_API_KEY="${ELEVENLABS_API_KEY:-}"
export ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-pNInz6obpgDQGcFmaJgB}"
export JARVIS_WHISPER_MODEL="${JARVIS_WHISPER_MODEL:-base}"
cd "$JARVIS_DIR"
python3 main.py
SCRIPT

chmod +x "$LAUNCHER"
echo "  ✓ Launcher script: $LAUNCHER"

# Create LaunchAgent plist
cat > "$PLIST" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$LAUNCHER</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/jarvis.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/jarvis.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>LSUIElement</key>
        <string>1</string>
    </dict>
</dict>
</plist>
PLIST

echo "  ✓ LaunchAgent plist: $PLIST"

# Unload if already loaded
launchctl unload "$PLIST" 2>/dev/null

# Load it
launchctl load "$PLIST" && echo "  ✓ LaunchAgent registered"

# Start immediately
launchctl start com.jarvis.assistant && echo "  ✓ JARVIS starting now..."

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  JARVIS will now auto-start on every login.  ║"
echo "║                                              ║"
echo "║  To disable:                                 ║"
echo "║  launchctl unload ~/Library/LaunchAgents/    ║"
echo "║             com.jarvis.assistant.plist       ║"
echo "║                                              ║"
echo "║  Logs: cat /tmp/jarvis.error.log             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
