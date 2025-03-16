"""
Wake Word Listener — detects "wake up, daddy's home" using Whisper
"""
import os
import time
import threading
import tempfile
import numpy as np
from typing import Callable, Optional


class WakeWordListener:
    """
    Continuously listens in the background for the wake phrase.
    When detected, calls on_wake() callback.
    """
    WAKE_PHRASE = "wake up, daddy's home"
    SAMPLE_RATE = 16000
    CHUNK_SECS  = 2.0

    def __init__(self, on_wake: Callable, audio_engine=None):
        self.on_wake     = on_wake
        self.audio_engine = audio_engine
        self._running    = False
        self._paused     = False
        self._thread     = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[JARVIS] Wake word listener started.")

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False

    def _listen_loop(self):
        raise NotImplementedError
