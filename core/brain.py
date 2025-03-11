"""
JARVIS Brain — stub
"""
import os
import anthropic

JARVIS_SYSTEM_PROMPT = """You are J.A.R.V.I.S. You serve your creator, referred to as Boss."""


class JarvisBrain:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.conversation_history = []

    def think(self, user_input: str) -> str:
        raise NotImplementedError

    def clear_memory(self):
        self.conversation_history = []
