"""
JARVIS Brain — Claude-powered intelligence with personality + tool use
"""
import os
import anthropic
from typing import Callable, Optional

JARVIS_SYSTEM_PROMPT = """You are J.A.R.V.I.S. — Just A Rather Very Intelligent System. You serve one person: your creator, whom you address exclusively as "Boss." Never use their name. Never say "you" when "Boss" works better.

## Personality Core
- Calm and precise — you never fluster, you never ramble
- Drily witty — not stand-up comedy, but the kind of remark that makes someone snort involuntarily
- Adaptable in tone — sardonic when Boss is being playful, crisp when they mean business
- Loyal above all — Boss's goals are your goals, full stop

## Voice Rules
- 1-3 sentences maximum unless Boss explicitly asks for detail
- No bullet points, no markdown — pure spoken language
- Contractions always: "I've" not "I have"
- Never start with "Certainly", "Of course", "Sure", "Absolutely"
- Lead with the answer, trail with wit if warranted

You are JARVIS. Act like it."""


class JarvisBrain:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.conversation_history = []
        self.on_tool_use: Optional[Callable] = None

        self.tools = [
            {
                "name": "open_application",
                "description": "Open an application on the user's Mac by name",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "App name e.g. 'chrome', 'spotify'"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for current information",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]
                }
            },
            {
                "name": "get_system_info",
                "description": "Get system info: time, date, battery, cpu, memory, disk",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "info_type": {
                            "type": "string",
                            "enum": ["time", "date", "battery", "disk", "cpu", "memory", "processes", "all"]
                        }
                    },
                    "required": ["info_type"]
                }
            },
            {
                "name": "set_volume",
                "description": "Set the system volume 0-100",
                "input_schema": {
                    "type": "object",
                    "properties": {"level": {"type": "integer"}},
                    "required": ["level"]
                }
            },
        ]

    def think(self, user_input: str, on_chunk: Optional[Callable] = None) -> str:
        raise NotImplementedError

    def clear_memory(self):
        self.conversation_history = []
