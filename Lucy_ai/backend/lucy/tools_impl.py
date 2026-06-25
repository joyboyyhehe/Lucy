import os
import subprocess
import webbrowser
import psutil
import platform
from typing import Any, Dict
from lucy.tools import LucyTool, registry

class SystemInfoTool(LucyTool):
    name = "system_info"
    description = "Retrieve current local system health, including CPU load, memory utilization, and battery details."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def run(self) -> Dict[str, Any]:
        # CPU Info
        cpu_usage = psutil.cpu_percent(interval=0.5)
        # Memory Info
        memory = psutil.virtual_memory()
        # Battery Info
        battery = psutil.sensors_battery()
        battery_pct = battery.percent if battery else None
        is_plugged = battery.power_plugged if battery else None

        return {
            "status": "success",
            "system": platform.system(),
            "cpu_percent": cpu_usage,
            "memory": {
                "total_gb": round(memory.total / (1024 ** 3), 2),
                "used_gb": round(memory.used / (1024 ** 3), 2),
                "free_gb": round(memory.available / (1024 ** 3), 2),
                "percent": memory.percent
            },
            "battery": {
                "percent": battery_pct,
                "power_plugged": is_plugged
            }
        }


class OpenAppTool(LucyTool):
    name = "open_app"
    description = "Launch a local system application (e.g., vscode, chrome, notepad, calculator) based on common naming."
    parameters = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name or common abbreviation of the application to launch (e.g. 'chrome', 'vscode', 'notepad', 'calc')."
            }
        },
        "required": ["app_name"]
    }

    async def run(self, app_name: str) -> Dict[str, Any]:
        app_name = app_name.lower().strip()
        
        # Simple mapping for common app launches on Windows
        win_mapping = {
            "chrome": "chrome.exe",
            "vscode": "code",
            "vs code": "code",
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe"
        }

        executable = win_mapping.get(app_name, app_name)

        try:
            # Run application non-blocking
            subprocess.Popen(executable, shell=True)
            return {
                "status": "success",
                "message": f"Successfully launched {app_name} ({executable})"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to launch {app_name}: {str(e)}"
            }


class BrowserSearchTool(LucyTool):
    name = "browser_search"
    description = "Open the user's default browser and perform a web search or navigate directly to a website (e.g. youtube, github, google)."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search term or query (e.g. 'how to make a cake') or a direct destination."
            },
            "site": {
                "type": "string",
                "description": "Optional site search target (e.g., 'youtube', 'google', 'github', 'wikipedia').",
                "enum": ["google", "youtube", "github", "wikipedia"]
            }
        },
        "required": ["query"]
    }

    async def run(self, query: str, site: str = "google") -> Dict[str, Any]:
        query_clean = query.strip()
        
        # Navigate directly if a full URL is detected
        if query_clean.startswith(("http://", "https://", "www.")):
            url = query_clean if query_clean.startswith(("http://", "https://")) else f"https://{query_clean}"
        else:
            # Map queries with site parameters
            if site == "youtube":
                url = f"https://www.youtube.com/results?search_query={query_clean}"
            elif site == "github":
                url = f"https://github.com/search?q={query_clean}"
            elif site == "wikipedia":
                url = f"https://en.wikipedia.org/wiki/Special:Search?search={query_clean}"
            else:
                url = f"https://www.google.com/search?q={query_clean}"

        try:
            # Open URL in user's default browser
            webbrowser.open(url)
            return {
                "status": "success",
                "url": url,
                "message": f"Opened search for '{query}' on {site}."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to open browser search: {str(e)}"
            }

# Register all tools
registry.register(SystemInfoTool())
registry.register(OpenAppTool())
registry.register(BrowserSearchTool())
