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
        elif self.system == "Windows":
            for c in candidates:
                try:
                    subprocess.Popen(["start", c], shell=True)
                    return f"Opened {app_name}, Boss."
                except Exception:
                    continue
        # Universal fallback
        try:
            subprocess.Popen(["xdg-open", app_name_lower])
            return f"Attempting to launch {app_name}, Boss."
        except Exception:
            pass
        return f"I couldn't locate {app_name} on this system, Boss. It may not be installed."

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
        if not url.startswith(("http://", "https://", "ftp://")):
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

    def run_command(self, command: str) -> str:
        """Run a shell command safely"""
        dangerous = ["rm -rf /", "rm -rf ~", "mkfs", "dd if=/dev/zero", ":(){:|:&};:", "sudo rm -rf", "format c:"]
        for danger in dangerous:
            if danger in command:
                return "I won't execute that command, Boss. It's too destructive."
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip()
            error = result.stderr.strip()
            if output and error:
                return f"Output:\n{output}\n\nErrors:\n{error}"
            return output or error or "Command executed successfully, Boss."
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds, Boss."
        except Exception as e:
            return f"Command failed: {e}"

    def get_system_info(self, info_type: str) -> str:
        """Get system information"""
        import psutil
        now = datetime.datetime.now()
        results = {}
        if info_type in ("time", "all"):
            results["time"] = now.strftime("%I:%M %p")
        if info_type in ("date", "all"):
            results["date"] = now.strftime("%A, %B %d, %Y")
        if info_type in ("battery", "all"):
            try:
                bat = psutil.sensors_battery()
                if bat:
                    status = "charging" if bat.power_plugged else "discharging"
                    results["battery"] = f"{bat.percent:.0f}% ({status})"
                else:
                    results["battery"] = "No battery detected (desktop)"
            except Exception:
                results["battery"] = "Battery info unavailable"
        if info_type in ("cpu", "all"):
            try:
                results["cpu"] = f"{psutil.cpu_percent(interval=0.5):.1f}% usage"
            except Exception:
                results["cpu"] = "CPU info unavailable"
        if info_type in ("memory", "all"):
            try:
                mem = psutil.virtual_memory()
                results["memory"] = f"{mem.percent:.1f}% used ({mem.used//(1024**3):.1f}GB / {mem.total//(1024**3):.1f}GB)"
            except Exception:
                results["memory"] = "Memory info unavailable"
        if info_type in ("disk", "all"):
            try:
                disk = psutil.disk_usage('/')
                results["disk"] = f"{disk.percent:.1f}% used ({disk.used//(1024**3):.1f}GB / {disk.total//(1024**3):.1f}GB)"
            except Exception:
                results["disk"] = "Disk info unavailable"
        if info_type in ("processes", "all"):
            try:
                procs = [(p.info['pid'], p.info['name']) for p in psutil.process_iter(['pid','name']) if p.info['name']][:15]
                results["processes"] = ", ".join([f"{n}({pid})" for pid, n in procs])
            except Exception:
                results["processes"] = "Process list unavailable"
        if not results:
            return f"Unknown info type: {info_type}"
        return json.dumps(results, indent=2) if info_type == "all" else list(results.values())[0]

    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot"""
        try:
            from PIL import ImageGrab
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.screenshot_dir, f"{filename or 'screenshot'}_{timestamp}.png")
            ImageGrab.grab().save(path)
            return f"Screenshot saved to {path}"
        except ImportError:
            try:
                import datetime as dt
                timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
                subprocess.run(["scrot", path], check=True)
                return f"Screenshot saved to {path}"
            except Exception:
                return "Screenshot unavailable. Install Pillow: pip install Pillow"
        except Exception as e:
            return f"Screenshot failed: {e}"

    def list_directory(self, path: str) -> str:
        """List directory contents"""
        path = os.path.expanduser(path)
        try:
            entries = os.listdir(path)
            dirs = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))])
            files = sorted([e for e in entries if os.path.isfile(os.path.join(path, e))])
            result = f"Directory: {path}\n"
            if dirs:  result += f"Folders ({len(dirs)}): {', '.join(dirs[:20])}\n"
            if files: result += f"Files ({len(files)}): {', '.join(files[:20])}"
            return result
        except Exception as e:
            return f"Cannot list directory: {e}"

    def set_volume(self, level: int) -> str:
        """Set system volume 0-100"""
        level = max(0, min(100, level))
        try:
            if self.system == "Darwin":
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
            elif self.system == "Linux":
                subprocess.run(["amixer", "-q", "sset", "Master", f"{level}%"])
            return f"Volume set to {level}%, Boss."
        except Exception as e:
            return f"Volume control unavailable: {e}"

    def get_weather(self, location: str = "") -> str:
        """Get current weather using wttr.in (no API key needed)"""
        import urllib.request, urllib.parse
        try:
            loc = urllib.parse.quote(location.strip()) if location.strip() else ""
            url = f"https://wttr.in/{loc}?format=j1"
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/2.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            curr = data["current_condition"][0]
            temp_f = curr["temp_F"]; temp_c = curr["temp_C"]
            feels_f = curr["FeelsLikeF"]
            desc = curr["weatherDesc"][0]["value"]
            humidity = curr["humidity"]; wind_mph = curr["windspeedMiles"]
            area = data.get("nearest_area", [{}])[0]
            city = area.get("areaName", [{}])[0].get("value", "")
            country = area.get("country", [{}])[0].get("value", "")
            loc_str = f"{city}, {country}".strip(", ") if city else "your location"
            today = data.get("weather", [{}])[0]
            min_f = today.get("mintempF", "?"); max_f = today.get("maxtempF", "?")
            return (f"Weather for {loc_str}: {desc}. Currently {temp_f}°F ({temp_c}°C), "
                    f"feels like {feels_f}°F. Today's range: {min_f}–{max_f}°F. "
                    f"Humidity {humidity}%, wind {wind_mph} mph.")
        except Exception as e:
            return f"Weather unavailable: {e}"


    def get_clipboard(self) -> str:
        """Read current clipboard text content."""
        try:
            if self.system == "Darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                return result.stdout.strip() or "Clipboard is empty, Boss."
            elif self.system == "Linux":
                result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True)
                return result.stdout.strip() or "Clipboard is empty, Boss."
            return "Clipboard access not supported on this platform, Boss."
        except Exception as e:
            return f"Couldn't read clipboard: {e}"

    def set_clipboard(self, text: str) -> str:
        """Write text to the clipboard."""
        try:
            if self.system == "Darwin":
                subprocess.run(["pbcopy"], input=text.encode(), check=True)
                return "Copied to clipboard, Boss."
            elif self.system == "Linux":
                subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
                return "Copied to clipboard, Boss."
            return "Clipboard write not supported on this platform, Boss."
        except Exception as e:
            return f"Clipboard write failed: {e}"


    def create_reminder(self, message: str, minutes: int) -> str:
        """Schedule a macOS reminder notification after N minutes."""
        try:
            if self.system != "Darwin":
                return "Reminders are only supported on macOS right now, Boss."
            script = (
                f'delay {minutes * 60}\n'
                f'display notification "{message}" with title "JARVIS Reminder"'
            )
            subprocess.Popen(["osascript", "-e", script])
            return f"Reminder set for {minutes} minute{'s' if minutes != 1 else ''} from now, Boss."
        except Exception as e:
            return f"Couldn't set reminder: {e}"


    def get_battery_percentage(self) -> str:
        """Return battery percentage as a plain string."""
        try:
            if self.system == "Darwin":
                result = subprocess.run(
                    ["pmset", "-g", "batt"], capture_output=True, text=True
                )
                import re
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    pct = int(match.group(1))
                    status = "charging" if "AC Power" in result.stdout else "on battery"
                    return f"Battery at {pct}%, {status}, Boss."
            return self.get_system_info("battery")
        except Exception as e:
            return f"Couldn't check battery: {e}"
