import json
import os
import asyncio
from datetime import datetime

SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"
MODULES_LIST = [
    "DeepWork", 
    "Real-time Reading", 
    "Visual Vision", 
    "Memory Core", 
    "Auto-Correction", 
    "Voice Synthesis", 
    "Code Execution", 
    "Web Search"
]

class DatabaseManager:
    def __init__(self):
        self.channel_settings = {}
        self.global_settings = {
            "blocked_models": [],
            "deepwork_allowed": True,
            "error_log": {},
            "ssbaxys_manual_mode": False,
            "creator_mode": True,
            "log_channel_id": None,
            "hive_mind_instructions": [],
            "modules": {m: True for m in MODULES_LIST}
        }
        self.conversation_history = {}
        # Synchronous initial load is required before bot starts
        self._sync_load_settings()
        self._sync_load_history()

    def _sync_load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "channels" in data or "global" in data:
                        c_data = data.get("channels", {})
                        self.channel_settings = {int(k): v for k, v in c_data.items()}
                        self.global_settings.update(data.get("global", {}))
                    else:
                        # Old format
                        self.channel_settings = {int(k): v for k, v in data.items()}
                
                # Backfill
                for cid in self.channel_settings:
                    if "modules" not in self.channel_settings[cid]:
                        self.channel_settings[cid]["modules"] = {m: (True if m == "DeepWork" else False) for m in MODULES_LIST}
                
                if "modules" not in self.global_settings:
                    self.global_settings["modules"] = {m: True for m in MODULES_LIST}
                    
                print(f"[DB] Settings loaded. Channels: {len(self.channel_settings)}")
            except Exception as e:
                print(f"[DB ERROR] Failed to load settings: {e}")

    def _sync_load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    self.conversation_history = {int(k): v for k, v in raw_data.items()}
            except Exception as e:
                print(f"[DB ERROR] Failed to load history: {e}")

    async def save_settings(self):
        try:
            data = {"channels": self.channel_settings, "global": self.global_settings}
            tmp_file = SETTINGS_FILE + ".tmp"
            
            def _write():
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                os.replace(tmp_file, SETTINGS_FILE)
            
            await asyncio.to_thread(_write)
        except Exception as e:
            print(f"[DB ERROR] Failed to save settings: {e}")

    async def save_history(self):
        try:
            tmp_file = HISTORY_FILE + ".tmp"
            
            def _write():
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(self.conversation_history, f, indent=4, ensure_ascii=False)
                os.replace(tmp_file, HISTORY_FILE)
            
            await asyncio.to_thread(_write)
        except Exception as e:
            print(f"[DB ERROR] Failed to save history: {e}")

    async def get_channel_settings(self, channel_id: int):
        if channel_id not in self.channel_settings:
            self.channel_settings[channel_id] = {
                "enabled": False,
                "model": "Mistral Large",
                "deepwork": True,
                "modules": {m: (True if m == "DeepWork" else False) for m in MODULES_LIST}
            }
            await self.save_settings()
        return self.channel_settings[channel_id]

    async def log_api_error(self):
        today = datetime.now().strftime("%Y-%m-%d")
        error_log = self.global_settings.get("error_log", {})
        error_log[today] = error_log.get(today, 0) + 1
        self.global_settings["error_log"] = error_log
        await self.save_settings()

db = DatabaseManager()
