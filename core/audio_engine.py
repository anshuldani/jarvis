"""
AudioEngine — ElevenLabs TTS (primary) + Whisper STT
"""
import os, time, threading, tempfile, subprocess, asyncio
import numpy as np
from typing import Callable, Optional


def _detect_tts():
    if os.environ.get("ELEVENLABS_API_KEY", ""):
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
    for cmd in [["mpg123", "-q", path], ["afplay", path],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]]:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
            subprocess.run(cmd)
            return


def _play_pcm(pcm_bytes: bytes, sample_rate=22050, on_rms: Optional[Callable] = None):
    """Play raw PCM int16 bytes via sounddevice, feeding RMS to callback."""
    try:
        import sounddevice as sd
        arr = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if on_rms and len(arr) > 0:
            on_rms(float(np.sqrt(np.mean(arr**2))))
        sd.play(arr, sample_rate)
        sd.wait()
    except Exception as e:
        print(f"[JARVIS audio] PCM playback failed: {e}")


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
        self.on_listening_start = self.on_listening_stop = None
        self.on_transcription = self.on_speaking_start = self.on_speaking_stop = None
        self.on_response_ready = self.on_audio_level = self.on_error = None
        self._whisper = None

    def _get_whisper(self):
        if self._whisper is None:
            model_name = os.environ.get("JARVIS_WHISPER_MODEL", "base")
            try:
                from faster_whisper import WhisperModel
                print(f"[JARVIS] Loading Whisper ({model_name})...")
                self._whisper = ("faster", WhisperModel(model_name, device="cpu", compute_type="int8"))
                print("[JARVIS] Whisper ready.")
            except ImportError:
                try:
                    import whisper
                    self._whisper = ("openai", whisper.load_model(model_name))
                except ImportError:
                    self._whisper = ("none", None)
        return self._whisper

    def _transcribe(self, audio: np.ndarray, sr=16000) -> str:
        import wave
        kind, model = self._get_whisper()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        try:
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes((audio * 32767).astype(np.int16).tobytes())
            if kind == "faster":
                segs, _ = model.transcribe(tmp, language="en")
                return " ".join(s.text for s in segs).strip()
            elif kind == "openai":
                return model.transcribe(tmp)["text"].strip()
            return ""
        finally:
            try: os.unlink(tmp)
            except: pass

    def speak(self, text: str):
        raise NotImplementedError

    def record_and_process(self):
        raise NotImplementedError

    def process_text(self, text: str):
        def _run():
            if self.on_transcription: self.on_transcription(text)
            response = self.brain.think(text, on_chunk=self.on_response_ready)
            print(f"[JARVIS]: {response}")
            self.speak(response)
        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        self.is_listening = False
