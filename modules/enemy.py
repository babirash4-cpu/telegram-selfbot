import asyncio
import random
from typing import List
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError:
    Client = None
    filters = None
    Message = None
from config import Config
from database import db

# Default troll roasts
ROAST_TEXTS: List[str] = [
    "فشار نخور عزیزم آب یخ میل داری؟ 🧊😂",
    "صدات از ته چاه میاد یکم بلندتر داد بزن! 📢",
    "تلاش قشنگی بود ولی بازم ضایع شدی! 🤡",
    "انرژیتو برای چیزای مهم‌تر بذار نه چرت و پرت گفتن! 🥱",
    "به نظر میاد دوباره حالت گرفته شده! قرص ضد فشار بخور 💊",
    "حرفات ارزش پاسخ دادن نداره ولی محض خنده جوابت دادم! 🤣"
]

# Popular roast stickers file_ids / pack handles
DEFAULT_ROAST_STICKERS: List[str] = [
    "CAACAgIAAxkBAAEK...1",
    "CAACAgIAAxkBAAEK...2"
]

def register_enemy_handlers(app: Client):
    prefix = Config.PREFIX

    # Watcher for enemy messages in any group or private chat
    @app.on_message(~filters.me)
    async def enemy_watcher(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else 0
        if not user_id:
            return

        enemy_info = db.is_enemy(user_id)
        if not enemy_info:
            return

        mode = enemy_info.get("mode", "text")
        custom_val = enemy_info.get("value", "")

        try:
            await asyncio.sleep(random.uniform(0.5, 1.2))  # human-like delay
            if mode == "text":
                reply = custom_val if custom_val else random.choice(ROAST_TEXTS)
                await message.reply_text(reply)
            elif mode == "sticker":
                if custom_val:
                    await message.reply_sticker(custom_val)
                else:
                    await message.reply_text(random.choice(ROAST_TEXTS))
            elif mode == "voice" and custom_val:
                await message.reply_voice(custom_val)
            else:
                await message.reply_text(random.choice(ROAST_TEXTS))
        except Exception:
            pass

    # Command to add enemy
    @app.on_message(filters.me & filters.command(["enemy", "دشمن"], prefixes=prefix))
    async def cmd_add_enemy(client: Client, message: Message):
        db.increment_stat("commands_run")
        target_id = None
        target_name = "کاربر"
        mode = "text"
        val = ""

        if message.reply_to_message and message.reply_to_message.from_user:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            if len(message.command) > 1:
                mode = message.command[1].lower()
            if len(message.command) > 2:
                val = " ".join(message.command[2:])
        elif len(message.command) > 1 and message.command[1].isdigit():
            target_id = int(message.command[1])
            target_name = f"کاربر {target_id}"
            if len(message.command) > 2:
                mode = message.command[2].lower()
            if len(message.command) > 3:
                val = " ".join(message.command[3:])

        if not target_id:
            await message.edit_text(
                f"⚠️ **نحوه تعریف انمی (دشمن):**\n\n"
                f"۱. روی پیام شخص ریپلای کنید و بفرستید:\n`{prefix}enemy text`\n"
                f"۲. یا با آیدی عددی:\n`{prefix}enemy 12345678 text`\n\n"
                f"🎭 حالت‌های مجاز: `text`, `sticker`, `voice`"
            )
            return

        db.add_enemy(target_id, mode=mode, value=val)
        await message.edit_text(
            f"🎯 **کاربر به لیست دشمنان اضافه شد!**\n\n"
            f"👤 کاربر: {target_name} (`{target_id}`)\n"
            f"🎭 حالت پاسخ: **{mode}**\n"
            f"⚡ از این پس هر پیامی ارسال کند، سلف بات بلافاصله به او پاسخ می‌دهد."
        )

    # Command to remove enemy
    @app.on_message(filters.me & filters.command(["delenemy", "حذف_دشمن"], prefixes=prefix))
    async def cmd_del_enemy(client: Client, message: Message):
        db.increment_stat("commands_run")
        target_id = None

        if message.reply_to_message and message.reply_to_message.from_user:
            target_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1 and message.command[1].isdigit():
            target_id = int(message.command[1])

        if not target_id:
            await message.edit_text(f"⚠️ روی پیام شخص ریپلای کنید یا آیدی عددی او را وارد کنید:\n`{prefix}delenemy 12345678`")
            return

        db.remove_enemy(target_id)
        await message.edit_text(f"🕊️ کاربر `{target_id}` از لیست دشمنان حذف شد و صلح برقرار گشت!")

    # Command to list enemies
    @app.on_message(filters.me & filters.command(["enemylist", "لیست_دشمن"], prefixes=prefix))
    async def cmd_list_enemies(client: Client, message: Message):
        enemies = db.get_enemies()
        if not enemies:
            await message.edit_text("🕊️ هیچ کاربری در لیست دشمنان نیست. دنیایی پر از صلح و صفا!")
            return

        lines = ["⚔️ **لیست دشمنان فعال (انمی):**\n"]
        for uid, data in enemies.items():
            lines.append(f"• آیدی: `{uid}` | حالت: `{data.get('mode', 'text')}`")

        await message.edit_text("\n".join(lines))
