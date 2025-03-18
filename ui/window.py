"""
JARVIS Window v2 — Animated waveform UI, PyQt5/PyQt6 compatible
Supports system tray, hide-to-tray, and wake-word activation.
"""
import math, random, sys, threading

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QTextEdit, QLineEdit, QPushButton, QApplication, QSizePolicy,
        QSystemTrayIcon, QMenu)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QRect, QPoint
    from PyQt6.QtGui import (QPainter, QColor, QBrush, QPen, QFont,
        QLinearGradient, QPainterPath, QIcon, QPixmap, QAction)
    _Q6 = True
except ImportError:
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QTextEdit, QLineEdit, QPushButton, QApplication, QSizePolicy,
        QSystemTrayIcon, QMenu)
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QRect, QPoint
    from PyQt5.QtGui import (QPainter, QColor, QBrush, QPen, QFont,
        QLinearGradient, QPainterPath, QIcon, QPixmap)
    try:
        from PyQt5.QtWidgets import QAction
    except ImportError:
        from PyQt5.QtGui import QAction
    _Q6 = False

# Enum compat — PyQt6 requires fully qualified enum access
NoPen       = Qt.PenStyle.NoPen           if _Q6 else Qt.NoPen
NoBrush     = Qt.BrushStyle.NoBrush       if _Q6 else Qt.NoBrush
AlignCenter = Qt.AlignmentFlag.AlignCenter if _Q6 else Qt.AlignCenter
Antialias   = QPainter.RenderHint.Antialiasing if _Q6 else QPainter.Antialiasing
MoveEnd     = (lambda c: c.MoveOperation.End) if _Q6 else (lambda c: c.End)
LeftBtn     = Qt.MouseButton.LeftButton   if _Q6 else Qt.LeftButton
StrongFocus = Qt.FocusPolicy.StrongFocus  if _Q6 else Qt.StrongFocus
Key_Esc     = Qt.Key.Key_Escape           if _Q6 else Qt.Key_Escape
Key_Spc     = Qt.Key.Key_Space            if _Q6 else Qt.Key_Space

STATE_COLORS = {
    "idle":      QColor(0,   150, 255),
    "listening": QColor(0,   255, 150),
    "thinking":  QColor(255, 165,   0),
    "speaking":  QColor(0,   220, 255),
    "error":     QColor(255,  60,  60),
}
N_BARS = 40


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
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding if _Q6 else QSizePolicy.Expanding,
            QSizePolicy.Policy.Fixed     if _Q6 else QSizePolicy.Fixed
        )
        self._state  = "idle"
        self._bars   = [0.15] * N_BARS
        self._target = [0.15] * N_BARS
        self._t      = 0.0
        self._rms    = 0.0
        self._sweep  = 0
        self._color  = STATE_COLORS["idle"]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_state(self, state: str):
        self._state = state
        self._color = STATE_COLORS.get(state, STATE_COLORS["idle"])

    def set_audio_level(self, rms: float):
        self._rms = max(0.0, min(1.0, rms))

    def _tick(self):
        self._t += 0.06
        # Placeholder — animations added next
        self.update()

    def paintEvent(self, event):
        pass  # drawing added next

    def mousePressEvent(self, ev):
        if ev.button() == LeftBtn:
            self.clicked.emit()


class JarvisWindow(QWidget):
    def __init__(self, brain, audio):
        super().__init__()
        self.brain = brain
        self.audio = audio
        self.sig   = JarvisSignals()
        self._drag = None
        self._wake = None

        if _Q6:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                                Qt.WindowType.WindowStaysOnTopHint |
                                Qt.WindowType.Tool)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(420, 540)
        scr = QApplication.primaryScreen().geometry()
        self.move(scr.width() - 460, scr.height() - 580)
        self.show()

    def set_wake_listener(self, wake):
        self._wake = wake
