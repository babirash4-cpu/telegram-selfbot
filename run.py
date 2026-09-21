import asyncio
import logging
import os
import sys

try:
    from aiohttp import web
except ImportError:
    web = None

try:
    from pyrogram import Client
except ImportError:
    Client = None
from config import Config
from database import db
from self_client import create_self_client
from modules.helper_bot import register_helper_bot_handlers
from modules.clock import clock_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RailwaySelfBot")

async def start_health_server(port: int):
    """Micro HTTP server for Railway healthchecks and keep-alive"""
    if web is None:
        logger.info("aiohttp not installed; skipping health server.")
        return

    async def handle_ping(request):
        stats = db.get_stats()
        return web.json_response({
            "status": "online",
            "type": "Single-User Telegram SelfBot",
            "platform": "Railway.com",
            "stats": stats
        })

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Health server running on http://0.0.0.0:{port}")

async def main():
    print(r"""
======================================================
  🤖 Railway Telegram Single-User SelfBot
  ⚡ Clean, Fast, High-Performance & Fully Featured
======================================================
    """)

    if not Config.is_valid():
        logger.error(
            "❌ خطای متغیرهای محیطی: مقادیر API_ID, API_HASH, SESSION_STRING یا OWNER_ID تنظیم نشده‌اند!\n"
            "لطفاً فایل .env را تکمیل کنید یا در تب Variables در Railway مقادیر را وارد کنید."
        )
        sys.exit(1)

    # 1. Start Self-Bot User Client
    logger.info("🚀 در حال راه‌اندازی اکانت کاربری سلف بات...")
    self_app = create_self_client()
    await self_app.start()
    me = await self_app.get_me()
    logger.info(f"✅ سلف بات با اکانت [{me.first_name}] (@{me.username or 'بدون نام‌کاربری'}) متصل شد!")

    # Verify Owner ID
    if Config.OWNER_ID == 0:
        Config.OWNER_ID = me.id
        logger.info(f"👑 مالک به صورت خودکار با آیدی {me.id} تنظیم شد.")

    # 2. Start Helper Bot (if configured)
    helper_app = None
    if Config.BOT_TOKEN:
        logger.info("🤖 در حال راه‌اندازی ربات کمکی و پنل شیشه‌ای (Helper Bot)...")
        helper_app = Client(
            name="single_user_helper",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            in_memory=True
        )
        register_helper_bot_handlers(helper_app)
        await helper_app.start()
        bot_info = await helper_app.get_me()
        logger.info(f"✅ ربات هلپر با موفقیت فعال شد: @{bot_info.username}")

    # 3. Start Background Tasks
    asyncio.create_task(clock_worker(self_app))

    # 4. Optional Railway HTTP healthcheck
    port = int(os.getenv("PORT", str(Config.PORT)))
    try:
        await start_health_server(port)
    except Exception as e:
        logger.warning(f"⚠️ Health server could not bind to port {port}: {e}")

    logger.info("🌟 سلف بات تک کاربره شما با تمام امکانات آماده به کار است!")

    # Keep alive
    try:
        await asyncio.Event().wait()
    finally:
        if self_app:
            await self_app.stop()
        if helper_app:
            await helper_app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 سلف بات متوقف شد.")
