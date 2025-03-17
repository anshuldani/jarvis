"""
JARVIS Window v2 — Animated waveform UI, PyQt5/PyQt6 compatible
"""
import math
import random
import sys
import threading

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt6.QtGui import QPainter, QColor
    _Q6 = True
except ImportError:
    from PyQt5.QtWidgets import QWidget, QApplication
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QPainter, QColor
    _Q6 = False


class JarvisSignals(QObject):
    listening_start = pyqtSignal()
    listening_stop  = pyqtSignal()
    speaking_start  = pyqtSignal(str)
    speaking_stop   = pyqtSignal()
    transcription   = pyqtSignal(str)
    response_chunk  = pyqtSignal(str)
    tool_use        = pyqtSignal(str, dict)
    audio_level     = pyqtSignal(float)
    error           = pyqtSignal(str)
    wake_triggered  = pyqtSignal()


class WaveformWidget(QWidget):
    """40-bar animated waveform."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self._state = "idle"
        self._bars  = [0.15] * 40
        self._t     = 0.0

    def set_state(self, state: str):
        self._state = state

    def set_audio_level(self, rms: float):
        pass

    def paintEvent(self, event):
        pass


class JarvisWindow(QWidget):
    def __init__(self, brain, audio):
        super().__init__()
        self.brain = brain
        self.audio = audio
        self.sig   = JarvisSignals()
        self.resize(420, 540)
        self.show()
