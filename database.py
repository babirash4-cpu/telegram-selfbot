import json
import os
import threading
from typing import Any, Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "clock": {
        "enabled": False,
        "mode": "name",  # "name", "bio", or "both"
        "font_style": "bold",
        "custom_template": "• {time} •",
        "show_heart": True,
        "date_type": "jalali"  # "jalali" or "gregorian"
    },
    "anti_delete": {
        "enabled": True,
        "destination": "saved_messages",  # "saved_messages" or "helper_bot"
        "log_edits": True,
        "log_media": True,
        "whitelist_chats": []
    },
    "secretary": {
        "enabled": False,
        "afk": False,
        "afk_reason": "در حال حاضر در دسترس نیستم، به زودی پاسخ می‌دهم.",
        "cooldown_seconds": 300,
        "auto_reply_text": "سلام! من در حال حاضر آفلاین هستم. پیام شما دریافت شد و به زودی پاسخ می‌دهم.",
        "whitelist_users": [],
        "questionnaire_enabled": False
    },
    "casino": {
        "balance": 10000,
        "max_bet": 1000,
        "stop_loss": 500,
        "stats": {
            "wins": 0,
            "losses": 0,
            "total_won": 0,
            "total_lost": 0
        }
    },
    "enemies": {},  # str(user_id): {"mode": "sticker", "value": "pack_or_text"}
    "triggers": {},  # keyword: reply_text
    "stats": {
        "commands_run": 0,
        "anti_delete_caught": 0,
        "start_time": 0
    }
}

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(DATA_FILE):
            self._save_raw(DEFAULT_SETTINGS)

    def _load_raw(self) -> Dict[str, Any]:
        with self._lock:
            if not os.path.exists(DATA_FILE):
                return DEFAULT_SETTINGS.copy()
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with default settings to ensure new keys exist
                    for k, v in DEFAULT_SETTINGS.items():
                        if k not in data:
                            data[k] = v
                        elif isinstance(v, dict):
                            for sub_k, sub_v in v.items():
                                if sub_k not in data[k]:
                                    data[k][sub_k] = sub_v
                    return data
            except Exception:
                return DEFAULT_SETTINGS.copy()

    def _save_raw(self, data: Dict[str, Any]):
        with self._lock:
            temp_file = f"{DATA_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, DATA_FILE)

    # ---------------- Clock ----------------
    def get_clock(self) -> Dict[str, Any]:
        return self._load_raw().get("clock", DEFAULT_SETTINGS["clock"])

    def update_clock(self, **kwargs):
        data = self._load_raw()
        data["clock"].update(kwargs)
        self._save_raw(data)

    # ---------------- Anti-Delete ----------------
    def get_anti_delete(self) -> Dict[str, Any]:
        return self._load_raw().get("anti_delete", DEFAULT_SETTINGS["anti_delete"])

    def update_anti_delete(self, **kwargs):
        data = self._load_raw()
        data["anti_delete"].update(kwargs)
        self._save_raw(data)

    # ---------------- Secretary ----------------
    def get_secretary(self) -> Dict[str, Any]:
        return self._load_raw().get("secretary", DEFAULT_SETTINGS["secretary"])

    def update_secretary(self, **kwargs):
        data = self._load_raw()
        data["secretary"].update(kwargs)
        self._save_raw(data)

    # ---------------- Casino & Betting ----------------
    def get_casino(self) -> Dict[str, Any]:
        return self._load_raw().get("casino", DEFAULT_SETTINGS["casino"])

    def update_casino(self, **kwargs):
        data = self._load_raw()
        data["casino"].update(kwargs)
        self._save_raw(data)

    def record_bet(self, won: bool, amount: int):
        data = self._load_raw()
        stats = data["casino"]["stats"]
        if won:
            stats["wins"] += 1
            stats["total_won"] += amount
            data["casino"]["balance"] += amount
        else:
            stats["losses"] += 1
            stats["total_lost"] += amount
            data["casino"]["balance"] = max(0, data["casino"]["balance"] - amount)
        self._save_raw(data)

    # ---------------- Enemies ----------------
    def get_enemies(self) -> Dict[str, Any]:
        return self._load_raw().get("enemies", {})

    def add_enemy(self, user_id: int, mode: str = "sticker", value: str = ""):
        data = self._load_raw()
        data["enemies"][str(user_id)] = {"mode": mode, "value": value}
        self._save_raw(data)

    def remove_enemy(self, user_id: int):
        data = self._load_raw()
        uid = str(user_id)
        if uid in data["enemies"]:
            del data["enemies"][uid]
            self._save_raw(data)

    def is_enemy(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.get_enemies().get(str(user_id))

    # ---------------- Triggers (Auto-Reply) ----------------
    def get_triggers(self) -> Dict[str, str]:
        return self._load_raw().get("triggers", {})

    def add_trigger(self, keyword: str, response: str):
        data = self._load_raw()
        data["triggers"][keyword.strip().lower()] = response
        self._save_raw(data)

    def remove_trigger(self, keyword: str):
        data = self._load_raw()
        k = keyword.strip().lower()
        if k in data["triggers"]:
            del data["triggers"][k]
            self._save_raw(data)

    # ---------------- Stats ----------------
    def increment_stat(self, key: str, amount: int = 1):
        data = self._load_raw()
        if key in data["stats"]:
            data["stats"][key] += amount
        else:
            data["stats"][key] = amount
        self._save_raw(data)

    def get_stats(self) -> Dict[str, Any]:
        return self._load_raw().get("stats", DEFAULT_SETTINGS["stats"])

db = Database()
