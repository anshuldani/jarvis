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
            "firefox": ["firefox"], "safari": ["safari"],
            "vscode": ["code"], "vs code": ["code"],
            "terminal": ["gnome-terminal", "xterm", "Terminal"],
            "slack": ["slack"], "discord": ["discord"], "spotify": ["spotify"],
        }
        candidates = aliases.get(app_name_lower, [app_name, app_name_lower])
        if self.system == "Darwin":
            for c in candidates:
                try:
                    if subprocess.run(["open", "-a", c], capture_output=True).returncode == 0:
                        return f"Opened {app_name}, Boss."
                except Exception:
                    continue
            subprocess.Popen(["open", app_name])
            return f"Launched {app_name}, Boss."
        elif self.system == "Linux":
            for c in candidates:
                try:
                    subprocess.Popen([c], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Launched {app_name}, Boss."
                except FileNotFoundError:
                    continue
        return f"Couldn't locate {app_name}, Boss."

    def web_search(self, query: str) -> str:
        """Search the web using DuckDuckGo JSON API"""
        import urllib.request, urllib.parse
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/2.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            results = []
            if data.get("AbstractText"):
                results.append(data["AbstractText"][:500])
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(topic["Text"][:200])
            if results:
                return "\n\n".join(results)
            self.open_url(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return f"Opened browser search for '{query}', Boss."
        except Exception as e:
            return f"Search failed: {e}"

    def open_url(self, url: str) -> str:
        """Open URL in default browser"""
        if not url.startswith("http"):
            url = "https://" + url
        import webbrowser
        webbrowser.open(url)
        return f"Opened {url}, Boss."

    def get_system_info(self, info_type: str) -> str:
        raise NotImplementedError

    def set_volume(self, level: int) -> str:
        raise NotImplementedError

    def read_file(self, path: str) -> str:
        """Read file contents"""
        path = os.path.expanduser(path)
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if len(content) > 4000:
                return content[:4000] + f"\n\n[...truncated. {len(content)} chars total]"
            return content
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        path = os.path.expanduser(path)
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written: {path}"
        except Exception as e:
            return f"Error writing file: {e}"
