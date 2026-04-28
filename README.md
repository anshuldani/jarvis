# J.A.R.V.I.S. v2

> *"All systems nominal, Boss."*

Always-on desktop AI assistant: say the wake phrase, speak your request, get a voice response. Runs in the system tray, pops up on wake word, uses ElevenLabs for high-quality British TTS with three local fallbacks, and has 10 OS-level tools — open apps, search the web, take screenshots, control volume, check weather.

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
cp .env.example .env
# Fill in your API keys
bash setup.sh
python main.py
```

## Requirements
- Python 3.10+
- Anthropic API key
- ElevenLabs API key (optional, falls back to edge-tts)

## Voice Commands
Just say anything after waking JARVIS. Examples:
- "What time is it?"
- "Open Spotify"
- "What's the weather?"
- "Set volume to 50"
- "Take a screenshot"

## Architecture

```
main.py           Entry point — Qt app, wires all components
core/
  brain.py        Claude API integration, tool loop, JARVIS personality
  audio_engine.py STT (Whisper) + TTS (ElevenLabs/edge-tts/pyttsx3)
  wake_word.py    Background listener for wake phrase
ui/
  window.py       Animated waveform UI, tray icon, PyQt5/6 compat
tools/
  system_tools.py 10 OS tools: apps, web, files, system, weather
```

## Voice Engine
- **Primary TTS**: ElevenLabs `eleven_turbo_v2_5` — deep, British, low latency
- **Fallback 1**: `edge-tts` with `en-GB-RyanNeural`
- **Fallback 2**: `pyttsx3` with system male voice
- **Fallback 3**: macOS `say` / Linux `espeak`

## Wake Phrase
> *"Wake up, daddy's home"*

Say this any time — JARVIS runs in the background and pops up automatically.
