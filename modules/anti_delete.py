import asyncio
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Optional, Tuple
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError:
    Client = None
    filters = None
    Message = None
from config import Config
from database import db

# Ring buffer for recent messages: (chat_id, message_id) -> dict with text/media info
MAX_CACHED_MESSAGES = 1000
message_cache: "OrderedDict[Tuple[int, int], Dict]" = OrderedDict()

def cache_message(message: Message):
    key = (message.chat.id, message.id)
    sender = message.from_user
    sender_name = f"{sender.first_name} {sender.last_name or ''}".strip() if sender else "نامشخص"
    sender_id = sender.id if sender else 0
    username = f"@{sender.username}" if sender and sender.username else "ندارد"

    media_type = None
    media_file_id = None
    if message.photo:
        media_type = "photo"
        media_file_id = message.photo.file_id
    elif message.voice:
        media_type = "voice"
        media_file_id = message.voice.file_id
    elif message.audio:
        media_type = "audio"
        media_file_id = message.audio.file_id
    elif message.video:
        media_type = "video"
        media_file_id = message.video.file_id
    elif message.document:
        media_type = "document"
        media_file_id = message.document.file_id

    message_cache[key] = {
        "text": message.text or message.caption or "",
        "sender_name": sender_name,
        "sender_id": sender_id,
        "username": username,
        "chat_id": message.chat.id,
        "chat_title": message.chat.title or "چت خصوصی",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "media_type": media_type,
        "media_file_id": media_file_id
    }

    if len(message_cache) > MAX_CACHED_MESSAGES:
        message_cache.popitem(last=False)

def register_anti_delete_handlers(app: Client):
    prefix = Config.PREFIX

    # Cache incoming messages
    @app.on_message(~filters.me, group=-1)
    async def msg_cache_watcher(client: Client, message: Message):
        cache_message(message)

    # Monitor edited messages
    @app.on_edited_message(~filters.me)
    async def edited_message_watcher(client: Client, message: Message):
        ad_conf = db.get_anti_delete()
        if not ad_conf.get("enabled", True) or not ad_conf.get("log_edits", True):
            return

        key = (message.chat.id, message.id)
        cached = message_cache.get(key)
        if not cached:
            return

        old_text = cached.get("text", "")
        new_text = message.text or message.caption or ""

        if old_text == new_text:
            return

        log_text = (
            f"✏️ **پیام ویرایش شده کشف شد!**\n\n"
            f"👤 فرستنده: {cached['sender_name']} (`{cached['sender_id']}`) [{cached['username']}]\n"
            f"💬 چت: {cached['chat_title']} (`{cached['chat_id']}`)\n"
            f"⏰ زمان ثبت: `{cached['date']}`\n\n"
            f"📄 **متن قبلی:**\n`{old_text}`\n\n"
            f"🆕 **متن جدید:**\n`{new_text}`"
        )

        db.increment_stat("anti_delete_caught")
        target = "me"
        try:
            await client.send_message(target, log_text)
        except Exception:
            pass

        # Update cache with new text
        cached["text"] = new_text

    # Monitor deleted messages
    @app.on_deleted_messages()
    async def deleted_message_watcher(client: Client, messages: list):
        ad_conf = db.get_anti_delete()
        if not ad_conf.get("enabled", True):
            return

        for msg in messages:
            key = (msg.chat.id, msg.id)
            cached = message_cache.get(key)
            if not cached:
                continue

            # Don't log our own messages or actions inside Saved Messages
            if cached.get("sender_id") == Config.OWNER_ID or cached.get("chat_id") == Config.OWNER_ID:
                continue

            db.increment_stat("anti_delete_caught")
            caption_info = (
                f"🗑️ **پیام حذف شده رهگیری شد!**\n\n"
                f"👤 فرستنده: {cached['sender_name']} (`{cached['sender_id']}`) [{cached['username']}]\n"
                f"💬 چت: {cached['chat_title']} (`{cached['chat_id']}`)\n"
                f"⏰ زمان: `{cached['date']}`\n"
            )

            target = "me"
            try:
                if cached.get("media_type") and cached.get("media_file_id"):
                    m_type = cached["media_type"]
                    f_id = cached["media_file_id"]
                    cap = f"{caption_info}\n📄 متن همراه مدیا:\n`{cached['text']}`" if cached['text'] else caption_info

                    if m_type == "photo":
                        await client.send_photo(target, f_id, caption=cap)
                    elif m_type == "voice":
                        await client.send_voice(target, f_id, caption=cap)
                    elif m_type == "audio":
                        await client.send_audio(target, f_id, caption=cap)
                    elif m_type == "video":
                        await client.send_video(target, f_id, caption=cap)
                    elif m_type == "document":
                        await client.send_document(target, f_id, caption=cap)
                else:
                    full_log = f"{caption_info}\n📄 **متن پیام حذف شده:**\n`{cached['text']}`"
                    await client.send_message(target, full_log)
            except Exception:
                pass

    # Command to toggle anti-delete
    @app.on_message(filters.me & filters.command(["antidelete", "آنتی_دلیت"], prefixes=prefix))
    async def cmd_toggle_antidelete(client: Client, message: Message):
        db.increment_stat("commands_run")
        ad = db.get_anti_delete()
        new_state = not ad.get("enabled", True)
        db.update_anti_delete(enabled=new_state)

        state_fa = "🟢 فعال" if new_state else "🔴 غیرفعال"
        await message.edit_text(
            f"🛡️ **سیستم آنتی‌دلیت:**\n\n"
            f"وضعیت: {state_fa}\n"
            f"📌 مقصد لاگ‌ها: Saved Messages (پیام‌های ذخیره شده)\n"
            f"📝 ردیابی ادیت: {'فعال' if ad.get('log_edits') else 'غیرفعال'}\n"
            f"📸 ردیابی مدیا (عکس، ویس، فیلم): {'فعال' if ad.get('log_media') else 'غیرفعال'}"
        )
