# J.A.R.V.I.S. v2

> *"All systems nominal, Boss."*

A desktop AI assistant inspired by Iron Man's JARVIS.

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
