"""
System Tools - JARVIS's ability to interact with the OS
"""
import os
import sys
import subprocess
import platform
import datetime
import shutil
import json
from typing import Optional


class SystemTools:
    def __init__(self):
        self.system = platform.system()
        self.screenshot_dir = os.path.expanduser("~/Desktop/JARVIS_screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def open_application(self, app_name: str) -> str:
        raise NotImplementedError

    def web_search(self, query: str) -> str:
        raise NotImplementedError
