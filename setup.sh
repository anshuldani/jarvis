#!/bin/bash
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   J.A.R.V.I.S. v2 — INSTALLATION            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Qt — conda is more reliable on macOS
echo "[1/5] Installing Qt (via conda)..."
conda install -c conda-forge pyqt -y --quiet && echo "  ✓ PyQt installed"

# Core deps
echo "[2/5] Installing core deps..."
pip install anthropic sounddevice numpy psutil Pillow --quiet && echo "  ✓ Core deps installed"

# STT
echo "[3/5] Installing Whisper STT..."
pip install faster-whisper --quiet && echo "  ✓ faster-whisper installed"

# TTS
echo "[4/5] Installing TTS..."
pip install edge-tts --quiet && echo "  ✓ edge-tts installed (free fallback)"
echo "  ℹ  For premium voice: pip install elevenlabs"
echo "     Then add ELEVENLABS_API_KEY to your .env"

# Audio playback
echo "[5/5] Checking audio playback..."
if command -v mpg123 &>/dev/null; then
    echo "  ✓ mpg123 found"
elif command -v brew &>/dev/null; then
    brew install mpg123 --quiet && echo "  ✓ mpg123 installed"
else
    echo "  ⚠  mpg123 not found. Install Homebrew then: brew install mpg123"
fi

# .env setup
echo ""
if [ ! -f .env ]; then
    cp .env.example .env
    echo "╔══════════════════════════════════════════════╗"
    echo "║  ACTION REQUIRED                             ║"
    echo "║  Edit .env and add your ANTHROPIC_API_KEY   ║"
    echo "╚══════════════════════════════════════════════╝"
else
    echo "  ✓ .env found"
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  DONE. Run: python3 main.py                  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
