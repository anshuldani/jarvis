#!/usr/bin/env python3
"""J.A.R.V.I.S. v2 — Just A Rather Very Intelligent System"""
import sys
import os
from pathlib import Path

# Load .env if present
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    app = QApplication(sys.argv)
    print("[JARVIS] Qt6 loaded")
except ImportError:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    app = QApplication(sys.argv)
    print("[JARVIS] Qt5 loaded")

app.setQuitOnLastWindowClosed(False)
app.setApplicationName("J.A.R.V.I.S.")

from core.brain import JarvisBrain
from core.audio_engine import AudioEngine
from ui.window import JarvisWindow

brain  = JarvisBrain()
audio  = AudioEngine(brain)
window = JarvisWindow(brain, audio)

sys.exit(app.exec())
