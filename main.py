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

# Fix Qt platform plugin path
import site
for sp in site.getsitepackages():
    for qt_ver in ("PyQt6", "PyQt5"):
        plugin_path = os.path.join(sp, qt_ver, qt_ver.replace("PyQt", "Qt"), "plugins", "platforms")
        if os.path.isdir(plugin_path):
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", plugin_path)
            break

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    app = QApplication(sys.argv)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    print("[JARVIS] Qt6 loaded")
except ImportError:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    print("[JARVIS] Qt5 loaded")

app.setQuitOnLastWindowClosed(False)
app.setApplicationName("J.A.R.V.I.S.")

from core.brain import JarvisBrain
from core.audio_engine import AudioEngine
from core.wake_word import WakeWordListener
from ui.window import JarvisWindow

brain  = JarvisBrain()
audio  = AudioEngine(brain)
window = JarvisWindow(brain, audio)

def _on_wake():
    window.sig.wake_triggered.emit()

wake = WakeWordListener(on_wake=_on_wake, audio_engine=audio)
window.set_wake_listener(wake)
wake.start()

print("\n" + "=" * 52)
print("  J.A.R.V.I.S. v2 ONLINE (background mode)")
print("  Say: 'wake up, daddy's home' to activate")
print("  Tray icon → Show / Quit")
print("=" * 52 + "\n")

sys.exit(app.exec())
