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

# Waveform bar colors per state
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
        rms = self._rms
        if self._state == "idle":
            for i in range(N_BARS):
                phase = (i / N_BARS) * 2 * 3.14159
                self._target[i] = 0.08 + 0.12 * abs(math.sin(self._t * 0.8 + phase))
        elif self._state == "listening":
            center = N_BARS / 2
            for i in range(N_BARS):
                dist  = abs(i - center) / center
                env   = 1.0 - dist * 0.5
                noise = random.uniform(0.85, 1.15)
                self._target[i] = max(0.05, min(0.95,
                    0.05 + rms * 6 * env * noise + 0.04 * abs(math.sin(self._t * 4 + i * 0.3))
                ))
        elif self._state == "thinking":
            self._sweep = (self._sweep + 1) % N_BARS
            for i in range(N_BARS):
                dist = min(abs(i - self._sweep), N_BARS - abs(i - self._sweep))
                glow = max(0, 1 - dist / 6)
                self._target[i] = 0.08 + glow * 0.82
        elif self._state == "speaking":
            for i in range(N_BARS):
                phase = (i / N_BARS) * math.pi * 4
                wave  = abs(math.sin(self._t * 6 + phase))
                self._target[i] = max(0.05, min(0.95,
                    0.1 + (rms * 5 + 0.3) * wave + random.uniform(0, 0.05)
                ))
        for i in range(N_BARS):
            self._bars[i] += (self._target[i] - self._bars[i]) * 0.30  # lower = smoother
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(Antialias)
        w, h = self.width(), self.height()
        total_bar_w = N_BARS * 6 + (N_BARS - 1) * 4
        x0 = (w - total_bar_w) // 2
        pad = 6
        c = self._color
        for i, amp in enumerate(self._bars):
            bar_h = max(4, int((h - pad * 2) * amp))
            bx = x0 + i * 10
            by = (h - bar_h) // 2
            grad = QLinearGradient(bx, by, bx, by + bar_h)
            core = QColor(c.red(), c.green(), c.blue(), 220)
            dim  = QColor(c.red(), c.green(), c.blue(), 60)
            grad.setColorAt(0.0, dim); grad.setColorAt(0.3, core)
            grad.setColorAt(0.7, core); grad.setColorAt(1.0, dim)
            p.setPen(NoPen); p.setBrush(QBrush(grad))
            path = QPainterPath()
            radius = min(3, bar_h // 2)
            path.addRoundedRect(bx, by, 6, bar_h, radius, radius)
            p.drawPath(path)
        p.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 25), 1))
        p.drawLine(0, h // 2, w, h // 2)

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
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(420, 540)
        scr = QApplication.primaryScreen().geometry()
        self.move(scr.width() - 460, scr.height() - 580)

        self._build_ui()
        self._wire_signals()
        self._wire_audio()
        self._build_tray()

        QTimer.singleShot(200, self.show)
        QTimer.singleShot(500, self._silent_boot)

    def set_wake_listener(self, wake):
        self._wake = wake

    # ── System tray ────────────────────────────────────────────────────────────

    def _build_tray(self):
        try:
            icon = self._make_tray_icon()
            self._tray = QSystemTrayIcon(icon, self)
            menu = QMenu()
            act_show = QAction("Show JARVIS", self)
            act_show.triggered.connect(self._show_window)
            act_quit = QAction("Quit", self)
            act_quit.triggered.connect(QApplication.instance().quit)
            menu.addAction(act_show); menu.addSeparator(); menu.addAction(act_quit)
            self._tray.setContextMenu(menu)
            self._tray.setToolTip("J.A.R.V.I.S. — Listening for wake phrase")
            self._tray.activated.connect(self._tray_clicked)
            self._tray.show()
            print("[JARVIS] Tray icon active.")
        except Exception as e:
            print(f"[JARVIS] Tray icon unavailable: {e}")
            self._tray = None

    def _make_tray_icon(self) -> QIcon:
        pix = QPixmap(32, 32)
        pix.fill(QColor(0, 0, 0, 0))
        p = QPainter(pix)
        p.setRenderHint(Antialias)
        p.setPen(NoPen); p.setBrush(QColor(0, 130, 255, 210))
        p.drawEllipse(1, 1, 30, 30)
        p.setPen(QPen(QColor(255, 255, 255, 240), 1))
        font = QFont("Courier New", 15)
        if _Q6: font.setWeight(QFont.Weight.Bold)
        else:   font.setBold(True)
        p.setFont(font)
        if _Q6: p.drawText(pix.rect(), AlignCenter, "J")
        else:
            from PyQt5.QtCore import QRect as _R
            p.drawText(_R(0, 0, 32, 32), AlignCenter, "J")
        p.end()
        return QIcon(pix)

    def _tray_clicked(self, reason):
        if _Q6:
            trigger = QSystemTrayIcon.ActivationReason.Trigger
            dbl     = QSystemTrayIcon.ActivationReason.DoubleClick
        else:
            trigger = QSystemTrayIcon.Trigger
            dbl     = QSystemTrayIcon.DoubleClick
        if reason in (trigger, dbl):
            self._show_window()

    def _show_window(self):
        self.show(); self.raise_(); self.activateWindow()

    def _hide_to_tray(self):
        self.hide()
        if self._tray:
            self._tray.showMessage("J.A.R.V.I.S.",
                "Still listening, Boss. Say the wake phrase to bring me back.",
                QSystemTrayIcon.MessageIcon.Information if _Q6 else QSystemTrayIcon.Information, 2000)

    # ── Signal wiring ──────────────────────────────────────────────────────────

    def _wire_signals(self):
        self.sig.listening_start.connect(self._ui_listen_start)
        self.sig.listening_stop.connect(self._ui_listen_stop)
        self.sig.speaking_start.connect(self._ui_speak_start)
        self.sig.speaking_stop.connect(self._ui_speak_stop)
        self.sig.transcription.connect(self._ui_trans)
        self.sig.response_chunk.connect(self._ui_chunk)
        self.sig.tool_use.connect(self._ui_tool)
        self.sig.audio_level.connect(self._ui_level)
        self.sig.error.connect(self._ui_error)
        self.sig.wake_triggered.connect(self._on_wake)

    def _wire_audio(self):
        self.audio.on_listening_start = lambda: self.sig.listening_start.emit()
        self.audio.on_listening_stop  = lambda: self.sig.listening_stop.emit()
        self.audio.on_transcription   = lambda t: self.sig.transcription.emit(t)
        self.audio.on_speaking_start  = lambda t: self.sig.speaking_start.emit(t)
        self.audio.on_speaking_stop   = lambda: self.sig.speaking_stop.emit()
        self.audio.on_response_ready  = lambda c: self.sig.response_chunk.emit(c)
        self.audio.on_audio_level     = lambda r: self.sig.audio_level.emit(r)
        self.audio.on_error           = lambda e: self.sig.error.emit(e)
        self.brain.on_tool_use        = lambda n, i: self.sig.tool_use.emit(n, i)

    def _build_ui(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(18, 18, 18, 14)
        lo.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        self.lbl_title = QLabel("J.A.R.V.I.S.")
        self.lbl_title.setStyleSheet(
            "color:rgba(0,180,255,230);font-family:'Courier New',monospace;"
            "font-size:13px;font-weight:bold;letter-spacing:4px;")
        self.lbl_status = QLabel("● STANDBY")
        self.lbl_status.setStyleSheet(
            "color:rgba(255,165,0,200);font-family:'Courier New',monospace;"
            "font-size:10px;letter-spacing:1px;")
        _bs = ("QPushButton{background:transparent;color:rgba(255,255,255,90);border:none;font-size:13px;}"
               "QPushButton:hover{color:rgba(255,80,80,220);}")
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(22, 22); btn_x.setStyleSheet(_bs)
        btn_x.clicked.connect(self._hide_to_tray)
        btn_m = QPushButton("–")
        btn_m.setFixedSize(22, 22)
        btn_m.setStyleSheet(_bs.replace("rgba(255,80,80,220)", "rgba(255,255,255,200)"))
        btn_m.clicked.connect(self._toggle_collapse)
        hdr.addWidget(self.lbl_title); hdr.addStretch()
        hdr.addWidget(self.lbl_status); hdr.addSpacing(8)
        hdr.addWidget(btn_m); hdr.addWidget(btn_x)

        self.lbl_mode = QLabel("STANDBY")
        self.lbl_mode.setStyleSheet(
            "color:rgba(0,200,255,160);font-family:'Courier New',monospace;"
            "font-size:10px;letter-spacing:3px;")
        self.lbl_mode.setAlignment(AlignCenter)

        self.wave = WaveformWidget()
        self.wave.clicked.connect(self._activate_voice)

        self.lbl_hint = QLabel("click waveform · SPACE to speak · ESC to hide")
        self.lbl_hint.setStyleSheet(
            "color:rgba(255,255,255,50);font-family:'Courier New',monospace;font-size:9px;")
        self.lbl_hint.setAlignment(AlignCenter)

        self.tx = QTextEdit()
        self.tx.setReadOnly(True)
        self.tx.setStyleSheet(
            "QTextEdit{background:rgba(0,8,25,200);border:1px solid rgba(0,140,255,50);"
            "border-radius:8px;color:rgba(190,220,255,210);"
            "font-family:'Courier New',monospace;font-size:12px;padding:8px;"
            "selection-background-color:rgba(0,150,255,70);}")

        inp = QHBoxLayout(); inp.setSpacing(6)
        self.txt = QLineEdit()
        self.txt.setPlaceholderText("Type to JARVIS...")
        self.txt.setStyleSheet(
            "QLineEdit{background:rgba(0,12,35,210);border:1px solid rgba(0,140,255,70);"
            "border-radius:6px;color:rgba(215,235,255,220);"
            "font-family:'Courier New',monospace;font-size:12px;padding:6px 10px;}"
            "QLineEdit:focus{border:1px solid rgba(0,200,255,170);}")
        self.txt.returnPressed.connect(self._submit)
        _ibs = ("QPushButton{background:rgba(0,90,190,110);border:1px solid rgba(0,140,255,70);"
                "border-radius:6px;color:rgba(0,200,255,190);font-size:15px;}"
                "QPushButton:hover{background:rgba(0,130,255,150);}")
        b_mic = QPushButton("🎤"); b_mic.setFixedSize(36, 36); b_mic.setStyleSheet(_ibs)
        b_mic.clicked.connect(self._activate_voice)
        b_snd = QPushButton("⏎"); b_snd.setFixedSize(36, 36); b_snd.setStyleSheet(_ibs)
        b_snd.clicked.connect(self._submit)
        inp.addWidget(self.txt); inp.addWidget(b_mic); inp.addWidget(b_snd)

        bot = QHBoxLayout()
        b_clr = QPushButton("⟳  CLEAR")
        b_clr.setStyleSheet(
            "QPushButton{background:transparent;border:1px solid rgba(255,90,90,50);"
            "border-radius:4px;color:rgba(255,90,90,100);"
            "font-family:'Courier New',monospace;font-size:9px;padding:3px 8px;letter-spacing:1px;}"
            "QPushButton:hover{color:rgba(255,90,90,190);border-color:rgba(255,90,90,140);}")
        b_clr.clicked.connect(self._clear)
        self.lbl_mem = QLabel("0 msgs")
        self.lbl_mem.setStyleSheet(
            "color:rgba(255,255,255,50);font-family:'Courier New',monospace;font-size:9px;")
        bot.addWidget(b_clr); bot.addStretch(); bot.addWidget(self.lbl_mem)

        lo.addLayout(hdr); lo.addSpacing(4)
        lo.addWidget(self.lbl_mode)
        lo.addWidget(self.wave)
        lo.addWidget(self.lbl_hint)
        lo.addWidget(self.tx)
        lo.addLayout(inp); lo.addLayout(bot)

        self.setFocusPolicy(StrongFocus); self.setFocus()

    # ── UI state handlers ─────────────────────────────────────────────────────

    def _set_mode(self, text, color):
        self.lbl_mode.setText(text)
        self.lbl_mode.setStyleSheet(
            f"color:{color};font-family:'Courier New',monospace;"
            "font-size:10px;letter-spacing:3px;")

    def _set_status(self, text, color="rgba(0,200,100,200)"):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"color:{color};font-family:'Courier New',monospace;"
            "font-size:10px;letter-spacing:1px;")

    def _ui_listen_start(self):
        self.wave.set_state("listening")
        self._set_mode("LISTENING", "rgba(0,255,150,200)")
        self._set_status("● LISTENING", "rgba(0,255,150,200)")
        self._log("\n[BOSS]", "rgba(0,220,150,200)")

    def _ui_listen_stop(self):
        self.wave.set_state("thinking")
        self._set_mode("PROCESSING", "rgba(255,165,0,200)")
        self._set_status("● THINKING", "rgba(255,165,0,200)")

    def _ui_trans(self, t):
        self._log(f" {t}", "rgba(200,230,255,170)")
        self._log("\n[JARVIS]  ", "rgba(0,180,255,220)")

    def _ui_chunk(self, c):
        self._log(c, "rgba(140,205,255,200)")
        n = len(self.brain.conversation_history) // 2
        self.lbl_mem.setText(f"{n} msgs")

    def _ui_speak_start(self, _):
        self.wave.set_state("speaking")
        self._set_mode("SPEAKING", "rgba(0,220,255,210)")
        self._set_status("● SPEAKING", "rgba(0,220,255,200)")

    def _ui_speak_stop(self):
        self.wave.set_state("idle")
        self._set_mode("STANDBY", "rgba(0,200,255,160)")
        self._set_status("● ONLINE", "rgba(0,200,100,200)")
        if self._wake:
            QTimer.singleShot(2000, self._wake.resume)

    def _ui_tool(self, name, _):
        label = name.replace("_", " ").title()
        self.wave.set_state("thinking")
        self._log(f"\n   ↳ [{label}]", "rgba(255,165,0,140)")
        self._set_status(f"● {label.upper()}", "rgba(255,165,0,200)")

    def _ui_level(self, rms: float):
        self.wave.set_audio_level(rms)

    def _ui_error(self, e):
        self.wave.set_state("error")
        self._log(f"\n[ERR] {e}", "rgba(255,80,80,200)")
        self._set_status("● ERROR", "rgba(255,80,80,200)")
        QTimer.singleShot(3000, lambda: self._set_status("● ONLINE"))

    # ── Wake word activation ──────────────────────────────────────────────────

    def _on_wake(self):
        self._show_window()
        self.wave.set_state("thinking")
        self._set_status("● WAKING", "rgba(0,220,255,200)")
        self._set_mode("WAKING UP", "rgba(0,220,255,200)")
        self._log("\n[SYS] Wake phrase detected.", "rgba(0,200,255,130)")
        self._log("\n[JARVIS]  ", "rgba(0,180,255,220)")
        def _greet():
            try:
                response = self.brain.wake_greeting()
                self.sig.response_chunk.emit(response)
                self.audio.speak(response)
            except Exception as e:
                self.sig.error.emit(f"Wake greeting failed: {e}")
        threading.Thread(target=_greet, daemon=True).start()

    # ── Silent boot ───────────────────────────────────────────────────────────

    def _silent_boot(self):
        print("[JARVIS] Armed — waiting for wake phrase.")
        self._set_status("● ARMED", "rgba(0,200,100,200)")
        self._set_mode("SAY: WAKE UP, DADDY'S HOME", "rgba(0,200,255,160)")
        self._log("\n[SYS] J.A.R.V.I.S. v2.0 ONLINE",         "rgba(0,180,255,210)")
        self._log("\n[SYS] Wake word listener: ARMED",          "rgba(0,200,150,160)")
        self._log("\n[SYS] Say: 'wake up, daddy's home'",       "rgba(0,200,150,160)")
        self._log("\n[SYS] Or type below and press Enter.",     "rgba(100,150,200,120)")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _activate_voice(self):
        if not self.audio.is_listening and not self.audio.is_speaking:
            if self._wake: self._wake.pause()
            self.audio.record_and_process()

    def _submit(self):
        text = self.txt.text().strip()
        if not text: return
        self.txt.clear()
        self._log(f"\n[BOSS] {text}", "rgba(0,220,150,200)")
        self._log("\n[JARVIS]  ", "rgba(0,180,255,220)")
        self.wave.set_state("thinking")
        self._set_status("● THINKING", "rgba(255,165,0,200)")
        self.audio.process_text(text)

    def _clear(self):
        self.brain.clear_memory()
        self._log("\n[SYS] Memory wiped.", "rgba(255,200,0,100)")
        self.lbl_mem.setText("0 msgs")

    def _toggle_collapse(self):
        if self.tx.isVisible():
            self.tx.hide(); self.resize(420, 190)
        else:
            self.tx.show(); self.resize(420, 540)

    # ── Transcript helper ─────────────────────────────────────────────────────

    def _log(self, text, color="rgba(190,220,255,200)"):
        c = self.tx.textCursor()
        c.movePosition(MoveEnd(c))
        self.tx.setTextCursor(c)
        safe = (text.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace("\n", "<br>"))
        self.tx.insertHtml(
            f'<span style="color:{color};font-family:Courier New,monospace;font-size:12px;">' +
            f'{safe}</span>')
        c = self.tx.textCursor()
        c.movePosition(MoveEnd(c))
        self.tx.setTextCursor(c)
        self.tx.ensureCursorVisible()

    # ── Window painting ───────────────────────────────────────────────────────

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(Antialias)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        p.setPen(NoPen); p.setBrush(QBrush(QColor(2, 8, 20, 235)))
        p.drawPath(path)
        p.setPen(QPen(QColor(0, 140, 255, 70), 1)); p.setBrush(NoBrush)
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 13, 13)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor(0, 0, 0, 0)); g.setColorAt(0.25, QColor(0, 160, 255, 55))
        g.setColorAt(0.75, QColor(0, 160, 255, 55)); g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(QPen(QBrush(g), 1))
        p.drawLine(14, 1, self.width() - 14, 1)
        p.setPen(QPen(QColor(0, 170, 255, 90), 1.5))
        s, w, h = 16, self.width(), self.height()
        for x1, y1, x2, y2 in [
            (8,8,8+s,8),(8,8,8,8+s),(w-8-s,8,w-8,8),(w-8,8,w-8,8+s),
            (8,h-8,8+s,h-8),(8,h-8-s,8,h-8),(w-8-s,h-8,w-8,h-8),(w-8,h-8-s,w-8,h-8),
        ]:
            p.drawLine(x1, y1, x2, y2)

    # ── Keyboard + drag ───────────────────────────────────────────────────────

    def keyPressEvent(self, ev):
        if ev.key() == Key_Esc: self._hide_to_tray()
        elif ev.key() == Key_Spc and not self.txt.hasFocus(): self._activate_voice()
        else: super().keyPressEvent(ev)

    def mousePressEvent(self, ev):
        if ev.button() == LeftBtn:
            gp = ev.globalPosition().toPoint() if _Q6 else ev.globalPos()
            self._drag = gp - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if ev.buttons() == LeftBtn and self._drag:
            gp = ev.globalPosition().toPoint() if _Q6 else ev.globalPos()
            self.move(gp - self._drag)

    def mouseReleaseEvent(self, ev):
        self._drag = None

    def closeEvent(self, ev):
        ev.ignore(); self._hide_to_tray()
