import asyncio
import time
from typing import Dict
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError:
    Client = None
    filters = None
    Message = None
from config import Config
from database import db

# Cooldown memory: user_id -> timestamp of last auto-reply
secretary_cooldowns: Dict[int, float] = {}

def register_secretary_handlers(app: Client):
    prefix = Config.PREFIX

    # Private chat watcher for secretary and custom triggers
    @app.on_message(filters.private & ~filters.me & ~filters.bot)
    async def pv_secretary_watcher(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else 0
        if not user_id:
            return

        # Check custom triggers first
        text = (message.text or message.caption or "").strip().lower()
        triggers = db.get_triggers()
        if text in triggers:
            await message.reply_text(triggers[text])
            return

        # Check secretary
        sec_conf = db.get_secretary()
        if not sec_conf.get("enabled", False) and not sec_conf.get("afk", False):
            return

        if user_id in sec_conf.get("whitelist_users", []):
            return

        now = time.time()
        cooldown = sec_conf.get("cooldown_seconds", 300)
        last_sent = secretary_cooldowns.get(user_id, 0)

        if now - last_sent < cooldown:
            return

        # Prepare response
        if sec_conf.get("afk", False):
            reason = sec_conf.get("afk_reason", "در دسترس نیستم.")
            reply_body = (
                f"💤 **مالک اکانت در حالت آفلاین (AFK) است:**\n\n"
                f"📝 دلیل: `{reason}`\n"
                f"⏰ پیام شما دریافت شد و به محض آنلاین شدن پاسخ می‌دهند."
            )
        else:
            reply_body = sec_conf.get(
                "auto_reply_text",
                "سلام! پیام شما دریافت شد. در اولین فرصت پاسخ می‌دهم. 🌹"
            )

        secretary_cooldowns[user_id] = now
        await message.reply_text(reply_body)

    # Command to turn AFK on
    @app.on_message(filters.me & filters.command(["afk", "غیبت"], prefixes=prefix))
    async def cmd_afk(client: Client, message: Message):
        db.increment_stat("commands_run")
        reason = "در حال حاضر در دسترس نیستم."
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])

        db.update_secretary(afk=True, afk_reason=reason)
        await message.edit_text(
            f"💤 **حالت غیبت (AFK) فعال شد!**\n\n"
            f"📝 دلیل: `{reason}`\n"
            f"🤖 از این لحظه در چت‌های خصوصی به پیام‌ها به صورت خودکار پاسخ داده می‌شود.\n\n"
            f"💡 برای خاموش کردن: `{prefix}unafk`"
        )

    # Command to turn AFK off
    @app.on_message(filters.me & filters.command(["unafk", "آنلاین"], prefixes=prefix))
    async def cmd_unafk(client: Client, message: Message):
        db.increment_stat("commands_run")
        db.update_secretary(afk=False)
        await message.edit_text("✨ **حالت غیبت (AFK) غیرفعال شد.** به جمع آنلاین‌ها خوش آمدید!")

    # Command to toggle secretary
    @app.on_message(filters.me & filters.command(["secretary", "منشی"], prefixes=prefix))
    async def cmd_secretary(client: Client, message: Message):
        db.increment_stat("commands_run")
        sec = db.get_secretary()
        new_state = not sec.get("enabled", False)
        db.update_secretary(enabled=new_state)

        state_fa = "🟢 فعال" if new_state else "🔴 غیرفعال"
        await message.edit_text(
            f"🤖 **منشی هوشمند سلف بات:**\n\n"
            f"وضعیت: {state_fa}\n"
            f"تایم کول‌داون ارسال: {sec.get('cooldown_seconds', 300)} ثانیه\n"
            f"متن منشی:\n`{sec.get('auto_reply_text', '')}`"
        )

    # Trigger commands (Add/Delete/List auto-replies)
    @app.on_message(filters.me & filters.command(["addreply", "پاسخ"], prefixes=prefix))
    async def cmd_add_reply(client: Client, message: Message):
        if len(message.command) < 2 or "|" not in message.text:
            await message.edit_text(f"⚠️ نحوه استفاده:\n`{prefix}addreply کلمه کلیدی | متن پاسخ`")
            return

        parts = message.text.split(maxsplit=1)[1].split("|", 1)
        keyword = parts[0].strip()
        response = parts[1].strip()

        db.add_trigger(keyword, response)
        await message.edit_text(f"✅ پاسخ خودکار برای کلمه **{keyword}** ذخیره شد.")

    @app.on_message(filters.me & filters.command(["delreply", "حذف_پاسخ"], prefixes=prefix))
    async def cmd_del_reply(client: Client, message: Message):
        if len(message.command) < 2:
            await message.edit_text(f"⚠️ نحوه استفاده:\n`{prefix}delreply کلمه کلیدی`")
            return

        keyword = " ".join(message.command[1:]).strip()
        db.remove_trigger(keyword)
        await message.edit_text(f"🗑️ پاسخ خودکار برای کلمه **{keyword}** حذف شد.")

    @app.on_message(filters.me & filters.command(["replies", "لیست_پاسخ"], prefixes=prefix))
    async def cmd_list_replies(client: Client, message: Message):
        triggers = db.get_triggers()
        if not triggers:
            await message.edit_text("📭 هیچ پاسخ خودکاری تعریف نشده است.")
            return

        lines = ["📋 **لیست پاسخ‌های خودکار فعال:**\n"]
        for k, v in triggers.items():
            lines.append(f"• `{k}` ➔ `{v}`")

        await message.edit_text("\n".join(lines))
