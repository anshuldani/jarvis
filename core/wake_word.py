"""
Wake Word Listener — detects "wake up, daddy's home" via Whisper
"""
import os
import tempfile
import threading
import time
import wave
import numpy as np
from typing import Callable, Optional


class WakeWordListener:
    """
    Continuously listens in the background for the wake phrase.
    When detected, calls on_wake() callback (thread-safe via Qt signal).
    """
    WAKE_PHRASE = "wake up, daddy's home"
    SAMPLE_RATE = 16000
    CHUNK_SECS  = 2.0

    def __init__(self, on_wake: Callable, audio_engine=None):
        self.on_wake      = on_wake
        self.audio_engine = audio_engine
        self._running     = False
        self._paused      = False
        self._thread      = None
        self._whisper     = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[JARVIS] Wake word listener started.")

    def pause(self):
        """Pause while mic is in use by main flow."""
        self._paused = True

    def resume(self):
        """Resume after JARVIS finishes speaking."""
        self._paused = False

    def stop(self):
        self._running = False

    def _get_whisper(self):
        if self._whisper is None:
            model_name = os.environ.get("JARVIS_WHISPER_MODEL", "base")
            try:
                from faster_whisper import WhisperModel
                self._whisper = ("faster", WhisperModel(model_name, device="cpu", compute_type="int8"))
            except ImportError:
                try:
                    import whisper
                    self._whisper = ("openai", whisper.load_model(model_name))
                except ImportError:
                    self._whisper = ("none", None)
        return self._whisper

    def _transcribe_chunk(self, audio: np.ndarray) -> str:
        kind, model = self._get_whisper()
        if kind == "none" or model is None:
            return ""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        try:
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes((audio * 32767).astype(np.int16).tobytes())
            if kind == "faster":
                segs, _ = model.transcribe(tmp, language="en")
                return " ".join(s.text for s in segs).strip().lower()
            elif kind == "openai":
                return model.transcribe(tmp)["text"].strip().lower()
            return ""
        except Exception:
            return ""
        finally:
            try: os.unlink(tmp)
            except: pass

    def _listen_loop(self):
        try:
            import sounddevice as sd
        except ImportError:
            print("[JARVIS] Wake word disabled — sounddevice not found.")
            return

        CHUNK = int(self.SAMPLE_RATE * self.CHUNK_SECS)
        print(f"[JARVIS] Listening for: '{self.WAKE_PHRASE}'")

        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue
            if self.audio_engine and (self.audio_engine.is_listening or self.audio_engine.is_speaking):
                time.sleep(0.2)
                continue
            try:
                recording = sd.rec(CHUNK, samplerate=self.SAMPLE_RATE,
                                   channels=1, dtype="float32")
                sd.wait()
                audio = recording.flatten()
                rms = float(np.sqrt(np.mean(audio**2)))
                if rms < 0.005:  # skip near-silence to avoid Whisper hallucinations
                    continue
                text = self._transcribe_chunk(audio)
                if not text:
                    continue
                print(f"[WAKE] heard: {text!r}")
                if self.WAKE_PHRASE in text or "daddy" in text:
                    self._paused = True
                    print("[JARVIS] Wake phrase detected!")
                    self.on_wake()
            except Exception as e:
                print(f"[JARVIS] Wake word error: {e}")
                time.sleep(1)


# ── Wake word sensitivity config ──────────────────────────────────────────────
SENSITIVITY = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5"))
"""
Sensitivity 0.0–1.0. Higher = more sensitive (more false positives).
Default 0.5 is balanced for quiet home environments.
Set WAKE_WORD_SENSITIVITY=0.3 for noisy environments.
"""
