import asyncio
import logging
try:
    from pyrogram import Client
except ImportError:
    Client = None
from config import Config
from modules.casino import register_casino_handlers
from modules.anti_delete import register_anti_delete_handlers
from modules.clock import register_clock_handlers, clock_worker
from modules.secretary import register_secretary_handlers
from modules.enemy import register_enemy_handlers
from modules.tools import register_tools_handlers

logger = logging.getLogger("SelfBot")

def create_self_client() -> Client:
    app = Client(
        name="single_user_self",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        session_string=Config.SESSION_STRING,
        in_memory=True
    )

    # Register handlers
    register_tools_handlers(app)
    register_casino_handlers(app)
    register_anti_delete_handlers(app)
    register_clock_handlers(app)
    register_secretary_handlers(app)
    register_enemy_handlers(app)

    return app
