"""
AudioEngine — ElevenLabs TTS (primary) + Whisper STT
Streams audio chunks for low latency, feeds RMS back to UI waveform
"""
import os, time, threading, tempfile, subprocess, asyncio
import numpy as np
from typing import Callable, Optional


def _detect_tts():
    if os.environ.get("ELEVENLABS_API_KEY", ""):
        try:
            import elevenlabs; return "elevenlabs"
        except ImportError: pass
    try:
        import edge_tts; return "edge_tts"
    except ImportError: pass
    try:
        import pyttsx3; return "pyttsx3"
    except ImportError: pass
    return "system"


def _play_mp3(path: str):
    for cmd in [["mpg123", "-q", path], ["afplay", path],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]]:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
            subprocess.run(cmd); return


def _play_pcm(pcm_bytes: bytes, sample_rate=22050, on_rms: Optional[Callable] = None):
    try:
        import sounddevice as sd
        arr = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if on_rms and len(arr) > 0: on_rms(float(np.sqrt(np.mean(arr**2))))
        sd.play(arr, sample_rate); sd.wait()
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
                    print("[JARVIS] No Whisper found — using SpeechRecognition fallback")
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

    def record_and_process(self):
        def _run():
            try:
                import sounddevice as sd
                SR, CHUNK = 16000, 1024
                SILENCE_RMS = 0.01; SILENCE_SECS = 1.5; SPEECH_RMS = 0.015
                silence_limit = int(SILENCE_SECS * SR / CHUNK)
                self.is_listening = True
                if self.on_listening_start: self.on_listening_start()
                chunks, silence_n, started = [], 0, False
                t0 = time.time()
                with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=CHUNK) as stream:
                    while self.is_listening and (time.time() - t0) < 30:
                        data, _ = stream.read(CHUNK)
                        rms = float(np.sqrt(np.mean(data**2)))
                        if self.on_audio_level: self.on_audio_level(min(rms * 8, 1.0))
                        if not started:
                            if rms > SPEECH_RMS: started = True
                            elif time.time() - t0 > 8: break
                            continue
                        chunks.append(data.copy())
                        silence_n = (silence_n + 1) if rms < SILENCE_RMS else 0
                        if silence_n >= silence_limit: break
                self.is_listening = False
                if self.on_listening_stop: self.on_listening_stop()
                if self.on_audio_level: self.on_audio_level(0.0)
                if not chunks: return
                audio = np.concatenate(chunks).flatten()
                text = self._transcribe(audio, SR)
                if not text.strip(): return
                print(f"[BOSS]: {text}")
                if self.on_transcription: self.on_transcription(text)
                response = self.brain.think(text, on_chunk=self.on_response_ready)
                print(f"[JARVIS]: {response}")
                self.speak(response)
            except ImportError:
                if self.on_error: self.on_error("sounddevice not installed. Run: pip install sounddevice")
            except Exception as e:
                self.is_listening = False
                if self.on_listening_stop: self.on_listening_stop()
                if self.on_error: self.on_error(str(e))
        threading.Thread(target=_run, daemon=True).start()

    def process_text(self, text: str):
        def _run():
            if self.on_transcription: self.on_transcription(text)
            response = self.brain.think(text, on_chunk=self.on_response_ready)
            print(f"[JARVIS]: {response}")
            self.speak(response)
        threading.Thread(target=_run, daemon=True).start()

    def speak(self, text: str):
        if not text.strip(): return
        def _run():
            self.is_speaking = True
            if self.on_speaking_start: self.on_speaking_start(text)
            try:
                if self._tts == "elevenlabs": self._speak_elevenlabs(text)
                elif self._tts == "edge_tts": self._speak_edge(text)
                elif self._tts == "pyttsx3":  self._speak_pyttsx3(text)
                else:                         self._speak_system(text)
            except Exception as e:
                print(f"[JARVIS TTS] {e} — falling back to print")
                print(f"[JARVIS]: {text}")
            finally:
                self.is_speaking = False
                if self.on_speaking_stop: self.on_speaking_stop()
                if self.on_audio_level: self.on_audio_level(0.0)
        threading.Thread(target=_run, daemon=True).start()

    def _speak_elevenlabs(self, text: str):
        key = os.environ.get("ELEVENLABS_API_KEY", "")
        vid = self.ELEVEN_VOICE_ID
        mdl = self.ELEVEN_MODEL
        # Try new SDK (1.x) first
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings
            client = ElevenLabs(api_key=key)
            audio_bytes = b"".join(client.generate(
                text=text, voice=vid, model=mdl,
                voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.85,
                                             style=0.3, use_speaker_boost=True)
            ))
            _play_pcm(audio_bytes, on_rms=self.on_audio_level)
            return
        except Exception:
            pass
        # Old SDK (0.x)
        try:
            from elevenlabs import generate, set_api_key, Voice, VoiceSettings
            set_api_key(key)
            audio = generate(
                text=text,
                voice=Voice(voice_id=vid, settings=VoiceSettings(
                    stability=0.4, similarity_boost=0.85, style=0.3, use_speaker_boost=True)),
                model=mdl, stream=False
            )
            _play_pcm(audio if isinstance(audio, bytes) else b"".join(audio),
                      on_rms=self.on_audio_level)
            return
        except Exception as e:
            print(f"[JARVIS] ElevenLabs failed: {e}, falling back to edge-tts")
            self._speak_edge(text)

    def _speak_edge(self, text: str):
        import edge_tts
        async def _go():
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name
            try:
                await edge_tts.Communicate(text, self.EDGE_VOICE).save(tmp)
                if self.on_audio_level: self.on_audio_level(0.6)
                _play_mp3(tmp)
            finally:
                try: os.unlink(tmp)
                except: pass
        asyncio.run(_go())

    def _speak_pyttsx3(self, text: str):
        import pyttsx3
        eng = pyttsx3.init()
        for v in eng.getProperty("voices"):
            if "male" in v.name.lower() or "david" in v.name.lower():
                eng.setProperty("voice", v.id); break
        eng.setProperty("rate", 170)
        eng.say(text); eng.runAndWait()

    def _speak_system(self, text: str):
        import platform
        if platform.system() == "Darwin":
            subprocess.run(["say", "-v", "Alex", text])
        elif platform.system() == "Linux":
            subprocess.run(["espeak", "-s", "160", text])
        else:
            print(f"[JARVIS]: {text}")

    def stop(self):
        self.is_listening = False
