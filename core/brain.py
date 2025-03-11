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
            {"name": "open_application", "description": "Open an app by name",
             "input_schema": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}},
            {"name": "web_search", "description": "Search the web",
             "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
            {"name": "open_url", "description": "Open a URL in the browser",
             "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
            {"name": "read_file", "description": "Read a file's contents",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
            {"name": "write_file", "description": "Write content to a file",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
            {"name": "run_command", "description": "Run a shell command",
             "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
            {"name": "get_system_info", "description": "Get system info",
             "input_schema": {"type": "object", "properties": {"info_type": {"type": "string", "enum": ["time","date","battery","disk","cpu","memory","processes","all"]}}, "required": ["info_type"]}},
            {"name": "take_screenshot", "description": "Take a screenshot",
             "input_schema": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": []}},
            {"name": "list_directory", "description": "List directory contents",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
            {"name": "set_volume", "description": "Set system volume 0-100",
             "input_schema": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]}},
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        from tools.system_tools import SystemTools
        tools = SystemTools()
        if self.on_tool_use:
            self.on_tool_use(tool_name, tool_input)
        try:
            dispatch = {
                "open_application": lambda: tools.open_application(tool_input["app_name"]),
                "web_search":       lambda: tools.web_search(tool_input["query"]),
                "open_url":         lambda: tools.open_url(tool_input["url"]),
                "read_file":        lambda: tools.read_file(tool_input["path"]),
                "write_file":       lambda: tools.write_file(tool_input["path"], tool_input["content"]),
                "run_command":      lambda: tools.run_command(tool_input["command"]),
                "get_system_info":  lambda: tools.get_system_info(tool_input["info_type"]),
                "take_screenshot":  lambda: tools.take_screenshot(tool_input.get("filename")),
                "list_directory":   lambda: tools.list_directory(tool_input["path"]),
                "set_volume":       lambda: tools.set_volume(tool_input["level"]),
            }
            return dispatch.get(tool_name, lambda: f"Unknown tool: {tool_name}")()
        except Exception as e:
            return f"Tool error: {e}"

    def think(self, user_input: str, on_chunk: Optional[Callable] = None) -> str:
        raise NotImplementedError

    def clear_memory(self):
        self.conversation_history = []
