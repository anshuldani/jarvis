"""
AudioEngine — ElevenLabs TTS (primary) + Whisper STT
Streams audio chunks for low latency, feeds RMS back to UI waveform
"""
import os, io, time, queue, threading, tempfile, subprocess, asyncio
import numpy as np
from typing import Callable, Optional


def _detect_tts():
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if key:
        try:
            import elevenlabs
            return "elevenlabs"
        except ImportError:
            pass
    try:
        import edge_tts
        return "edge_tts"
    except ImportError:
        pass
    try:
        import pyttsx3
        return "pyttsx3"
    except ImportError:
        pass
    return "system"


def _play_mp3(path: str):
    """Play an mp3 file using available system player."""
    for cmd in [["mpg123", "-q", path], ["afplay", path],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]]:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
            subprocess.run(cmd)
            return
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except Exception:
        pass


class AudioEngine:
    ELEVEN_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
    ELEVEN_MODEL    = "eleven_turbo_v2_5"
    EDGE_VOICE      = "en-GB-RyanNeural"

    def __init__(self, brain):
        self.brain = brain
        self.is_listening = False
        self.is_speaking  = False
        self._tts = _detect_tts()
        print(f"[JARVIS] TTS backend: {self._tts}")

        self.on_listening_start: Optional[Callable] = None
        self.on_listening_stop:  Optional[Callable] = None
        self.on_transcription:   Optional[Callable] = None
        self.on_speaking_start:  Optional[Callable] = None
        self.on_speaking_stop:   Optional[Callable] = None
        self.on_response_ready:  Optional[Callable] = None
        self.on_audio_level:     Optional[Callable] = None
        self.on_error:           Optional[Callable] = None
        self._whisper = None

    def speak(self, text: str):
        raise NotImplementedError

    def record_and_process(self):
        raise NotImplementedError

    def stop(self):
        self.is_listening = False
