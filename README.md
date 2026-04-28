# J.A.R.V.I.S. v2

> *"All systems nominal, Boss."*

Always-on desktop AI assistant: say the wake phrase, speak your request, get a voice response. Runs in the system tray, pops up on wake word, uses ElevenLabs for high-quality British TTS with three local fallbacks, and has 10 OS-level tools — open apps, search the web, take screenshots, control volume, check weather.

## Why this is hard

Four things have to run simultaneously without blocking each other: Porcupine wake word detection (reading the microphone continuously), the PyQt UI event loop (must stay responsive), Whisper speech-to-text (blocks until transcription finishes), and the LLM + TTS pipeline (network call → audio generation → playback). On a single thread, any one of them freezes the others.

The solution is three daemon threads: one for wake word detection, one for the LLM + tool loop, one for TTS streaming. All UI mutations go through Qt signals — no direct widget calls from background threads, which crash the app without a useful traceback.

The TTS fallback chain (ElevenLabs → edge-tts → pyttsx3 → macOS `say`) means the assistant never goes silent — but each fallback has a different audio pipeline, different latency profile, and different voice characteristics, so the code has to handle them uniformly without leaking fallback-specific state.

---

## Features
- Voice activation via custom wake phrase ("wake up, daddy's home")
- Whisper-powered speech-to-text
- ElevenLabs high-quality voice output (with edge-tts/pyttsx3 fallback)
- 10 built-in system tools: open apps, search web, run commands, system info, weather, screenshots
- Animated waveform UI with 4 states (idle/listening/thinking/speaking)
- Always-on-top floating window, frameless, draggable
- System tray integration — hides in background, reacts to wake phrase

## Setup

```bash
git clone https://github.com/anshuldani/jarvis
cd jarvis
bash setup.sh          # creates venv, installs dependencies
cp .env.example .env   # then fill in your keys
python main.py
```

Required env vars:

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...           # for Whisper STT
PORCUPINE_ACCESS_KEY=...        # for wake word detection
ELEVENLABS_API_KEY=...          # optional — falls back to edge-tts if absent
WEATHER_API_KEY=...             # optional — for weather tool (OpenWeatherMap)
```

**Requirements:** Python 3.10+, a microphone, PyQt5 or PyQt6 (auto-detected).

## Available tools

| Tool | Example command |
|---|---|
| Open application | "Open Spotify" / "Launch VS Code" |
| Web search | "Search for WWDC announcements" |
| Run shell command | "Run git status" |
| System info | "What's my CPU usage?" |
| Weather | "What's the weather in Chicago?" |
| Take screenshot | "Take a screenshot" |
| Set volume | "Set volume to 60" |
| Get current time | "What time is it?" |
| Get current date | "What's the date?" |
| Read clipboard | "What's in my clipboard?" |

The LLM decides which tool to call based on intent — no special syntax required. Say it naturally.

## Stack

| Component | Technology |
|---|---|
| LLM + personality | Anthropic API (tool use mode) |
| Speech-to-text | OpenAI Whisper API |
| Wake word | Porcupine (`pvporcupine`) |
| TTS primary | ElevenLabs `eleven_turbo_v2_5` — British, low latency |
| TTS fallback 1 | `edge-tts` with `en-GB-RyanNeural` |
| TTS fallback 2 | `pyttsx3` (local, offline) |
| TTS fallback 3 | macOS `say` / Linux `espeak` |
| UI | PyQt5/6 (auto-detected), animated waveform |
| System integration | System tray, always-on-top frameless window |

## Architecture

```
main.py           Entry point — Qt app, wires all components
core/
  brain.py        LLM API integration, tool loop, JARVIS personality
  audio_engine.py STT (Whisper) + TTS (ElevenLabs/edge-tts/pyttsx3)
  wake_word.py    Background listener for wake phrase
ui/
  window.py       Animated waveform UI, tray icon, PyQt5/6 compat
tools/
  system_tools.py 10 OS tools: apps, web, files, system, weather
```

## Wake phrase

> *"Wake up, daddy's home"*

JARVIS runs silently in the system tray. Say the wake phrase at any time — it pops up, confirms it's listening, and waits for your request. After responding it returns to the tray automatically.

To change the wake phrase, swap the Porcupine keyword in `core/wake_word.py`. Custom keywords require a Porcupine account but built-in keywords (like "jarvis", "computer", "hey siri") are free.
