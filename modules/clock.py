import asyncio
from datetime import datetime, timezone, timedelta

try:
    import pytz
except ImportError:
    pytz = None

try:
    from pyrogram import Client, filters
    from pyrogram.errors import FloodWait
    from pyrogram.types import Message
except ImportError:
    Client = None
    filters = None
    FloodWait = Exception
    Message = None
from config import Config
from database import db

# Number fonts
FONT_STYLES = {
    "persian": {"0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴", "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹"},
    "bold": {"0": "𝟎", "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗"},
    "mono": {"0": "𝟶", "1": "𝟷", "2": "𝟸", "3": "𝟹", "4": "𝟺", "5": "𝟻", "6": "𝟼", "7": "𝟽", "8": "𝟾", "9": "𝟿"},
    "bubble": {"0": "⓪", "1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤", "6": "⑥", "7": "⑦", "8": "⑧", "9": "⑨"},
    "italic": {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9"}
}

HEARTS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"]

def format_time(style: str = "bold", show_heart: bool = True) -> str:
    try:
        tz = pytz.timezone(Config.TZ)
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()

    hour_str = f"{now.hour:02d}"
    min_str = f"{now.minute:02d}"
    raw_time = f"{hour_str}:{min_str}"

    mapping = FONT_STYLES.get(style, FONT_STYLES["bold"])
    formatted = "".join(mapping.get(ch, ch) for ch in raw_time)

    heart = HEARTS[now.minute % len(HEARTS)] if show_heart else ""
    return f"{formatted} {heart}".strip()

async def clock_worker(app: Client):
    last_rendered = ""
    while True:
        try:
            clock_conf = db.get_clock()
            if clock_conf.get("enabled", False):
                style = clock_conf.get("font_style", "bold")
                show_heart = clock_conf.get("show_heart", True)
                mode = clock_conf.get("mode", "bio")  # "bio" or "name"
                time_str = format_time(style, show_heart)

                if time_str != last_rendered:
                    if mode in ["bio", "both"]:
                        custom_template = clock_conf.get("custom_template", "Online • {time}")
                        new_bio = custom_template.replace("{time}", time_str)
                        await app.update_profile(bio=new_bio[:70])

                    if mode in ["name", "both"]:
                        me = await app.get_me()
                        base_name = me.first_name.split("|")[0].strip()
                        new_name = f"{base_name} | {time_str}"
                        await app.update_profile(first_name=new_name[:64])

                    last_rendered = time_str
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

        await asyncio.sleep(45)

def register_clock_handlers(app: Client):
    prefix = Config.PREFIX

    @app.on_message(filters.me & filters.command(["clock", "ساعت"], prefixes=prefix))
    async def cmd_clock(client: Client, message: Message):
        db.increment_stat("commands_run")
        clock_conf = db.get_clock()
        new_state = not clock_conf.get("enabled", False)
        db.update_clock(enabled=new_state)

        state_fa = "🟢 فعال" if new_state else "🔴 غیرفعال"
        curr_time = format_time(clock_conf.get("font_style", "bold"))

        await message.edit_text(
            f"⏰ **ساعت خودکار سلف بات:**\n\n"
            f"وضعیت: {state_fa}\n"
            f"موقعیت: {clock_conf.get('mode', 'bio')}\n"
            f"فونت فعلی: `{clock_conf.get('font_style', 'bold')}`\n"
            f"نمونه ساعت زنده: **{curr_time}**\n\n"
            f"💡 دستورات تغییر فونت و حالت:\n"
            f"`{prefix}setclock font persian` (persian, bold, mono, bubble)\n"
            f"`{prefix}setclock mode bio` (bio, name, both)"
        )

    @app.on_message(filters.me & filters.command(["setclock"], prefixes=prefix))
    async def cmd_set_clock(client: Client, message: Message):
        if len(message.command) < 3:
            await message.edit_text(f"⚠️ دستور نامعتبر. مثال:\n`{prefix}setclock font bold`\n`{prefix}setclock mode bio`")
            return

        param = message.command[1].lower()
        val = message.command[2].lower()

        if param == "font":
            if val in FONT_STYLES:
                db.update_clock(font_style=val)
                sample = format_time(val)
                await message.edit_text(f"✅ فونت ساعت تغییر کرد به: **{val}** (نمونه: {sample})")
            else:
                await message.edit_text(f"❌ فونت‌های مجاز: {', '.join(FONT_STYLES.keys())}")
        elif param == "mode":
            if val in ["bio", "name", "both"]:
                db.update_clock(mode=val)
                await message.edit_text(f"✅ موقعیت نمایش ساعت تغییر کرد به: **{val}**")
            else:
                await message.edit_text("❌ حالت‌های مجاز: bio, name, both")
