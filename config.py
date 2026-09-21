import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    PREFIX = os.getenv("PREFIX", ".")
    TZ = os.getenv("TZ", "Asia/Tehran")
    PORT = int(os.getenv("PORT", "8080"))

    # Single-user safety check (API credentials required; OWNER_ID will auto-detect from session if 0)
    @classmethod
    def is_valid(cls) -> bool:
        return bool(cls.API_ID and cls.API_HASH and cls.SESSION_STRING)
