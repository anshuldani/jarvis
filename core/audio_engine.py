"""
AudioEngine — ElevenLabs TTS + Whisper STT stub
"""
import os
import threading
from typing import Callable, Optional


class AudioEngine:
    def __init__(self, brain):
        self.brain = brain
        self.is_listening = False
        self.is_speaking = False
        self.on_listening_start: Optional[Callable] = None
        self.on_listening_stop: Optional[Callable] = None
        self.on_transcription: Optional[Callable] = None
        self.on_speaking_start: Optional[Callable] = None
        self.on_speaking_stop: Optional[Callable] = None
        self.on_response_ready: Optional[Callable] = None
        self.on_audio_level: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def speak(self, text: str):
        raise NotImplementedError

    def record_and_process(self):
        raise NotImplementedError

    def stop(self):
        self.is_listening = False
