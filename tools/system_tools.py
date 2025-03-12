"""
System Tools - JARVIS's ability to interact with the OS
"""
import os
import subprocess
import platform
import datetime
import json
from typing import Optional


class SystemTools:
    def __init__(self):
        self.system = platform.system()
        self.screenshot_dir = os.path.expanduser("~/Desktop/JARVIS_screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def open_application(self, app_name: str) -> str:
        """Open an application by name"""
        app_name_lower = app_name.lower().strip()
        aliases = {
            "chrome": ["google-chrome", "google-chrome-stable", "chromium"],
            "firefox": ["firefox"],
            "safari": ["safari"],
            "vscode": ["code"],
            "vs code": ["code"],
            "terminal": ["gnome-terminal", "xterm", "konsole", "Terminal"],
            "slack": ["slack"],
            "discord": ["discord"],
            "spotify": ["spotify"],
            "finder": ["nautilus"],
        }
        candidates = aliases.get(app_name_lower, [app_name, app_name_lower])

        if self.system == "Darwin":
            for candidate in candidates:
                try:
                    result = subprocess.run(["open", "-a", candidate], capture_output=True, text=True)
                    if result.returncode == 0:
                        return f"Opened {app_name}, Boss."
                except Exception:
                    continue
            try:
                subprocess.Popen(["open", app_name])
                return f"Launched {app_name}, Boss."
            except Exception:
                pass
        elif self.system == "Linux":
            for candidate in candidates:
                try:
                    subprocess.Popen([candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Launched {app_name}, Boss."
                except FileNotFoundError:
                    continue

        return f"I couldn't locate {app_name} on this system, Boss."

    def web_search(self, query: str) -> str:
        raise NotImplementedError

    def get_system_info(self, info_type: str) -> str:
        raise NotImplementedError

    def set_volume(self, level: int) -> str:
        raise NotImplementedError
