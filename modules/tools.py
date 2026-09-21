import asyncio
import time
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError:
    Client = None
    filters = None
    Message = None
from config import Config
from database import db

START_TIME = time.time()

def get_uptime() -> str:
    elapsed = int(time.time() - START_TIME)
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days} روز")
    if hours > 0:
        parts.append(f"{hours} ساعت")
    if minutes > 0:
        parts.append(f"{minutes} دقیقه")
    parts.append(f"{seconds} ثانیه")
    return " و ".join(parts)

def register_tools_handlers(app: Client):
    prefix = Config.PREFIX

    # Ping / Status
    @app.on_message(filters.me & filters.command(["ping", "پینگ"], prefixes=prefix))
    async def cmd_ping(client: Client, message: Message):
        db.increment_stat("commands_run")
        start = time.time()
        await message.edit_text("🏓 در حال بررسی پینگ...")
        end = time.time()
        latency = round((end - start) * 1000, 2)
        stats = db.get_stats()

        await message.edit_text(
            f"⚡ **پینگ و وضعیت سلف بات:**\n\n"
            f"🚀 تاخیر پاسخ: **{latency} ms**\n"
            f"⏱ آپ‌تایم: **{get_uptime()}**\n"
            f"📊 تعداد دستورات اجرا شده: **{stats.get('commands_run', 0)}**\n"
            f"🛡️ پیام‌های ذخیره شده آنتی‌دلیت: **{stats.get('anti_delete_caught', 0)}**\n"
            f"☁️ میزبانی: **Railway.com** (تک کاربره، بهینه‌سازی شده)"
        )

    # Help Menu
    @app.on_message(filters.me & filters.command(["help", "راهنما"], prefixes=prefix))
    async def cmd_help(client: Client, message: Message):
        db.increment_stat("commands_run")
        p = prefix
        text = (
            f"🤖 **راهنمای جامع سلف بات پیشرفته تک کاربره:**\n\n"
            f"🎰 **کازینو و شرط‌بندی:**\n"
            f"• `{p}dice [مبلغ]` - پرتاب تاس جادویی 🎲\n"
            f"• `{p}dart [مبلغ]` - پرتاب دارت 🎯\n"
            f"• `{p}basket [مبلغ]` - پرتاب بسکتبال 🏀\n"
            f"• `{p}football [مبلغ]` - شوت فوتبال ⚽\n"
            f"• `{p}slot [مبلغ]` - گردونه اسلات ماشین 🎰\n"
            f"• `{p}bowling [مبلغ]` - پرتاب بولینگ 🎳\n"
            f"• `{p}balance` - مشاهده موجودی و آمار شرط‌ها\n"
            f"• `{p}setbalance [مقدار]` - تنظیم موجودی دلخواه\n\n"
            f"🛡️ **آنتی‌دلیت و ادیت:**\n"
            f"• `{p}antidelete` - خاموش/روشن کردن ردیاب پیام‌های پاک شده\n\n"
            f"⏰ **ساعت خودکار روی بیو و نام:**\n"
            f"• `{p}clock` - روشن/خاموش کردن ساعت\n"
            f"• `{p}setclock font [bold|persian|mono|bubble]`\n"
            f"• `{p}setclock mode [bio|name|both]`\n\n"
            f"🤖 **منشی و غیبت:**\n"
            f"• `{p}secretary` - روشن/خاموش کردن منشی\n"
            f"• `{p}afk [دلیل]` - فعال‌سازی حالت غیبت\n"
            f"• `{p}unafk` - غیرفعال‌سازی حالت غیبت\n"
            f"• `{p}addreply کلمه | پاسخ` - ثبت پاسخ سریع\n\n"
            f"⚔️ **سیستم انمی (دشمن):**\n"
            f"• `{p}enemy [text|sticker|voice]` (روی ریپلای)\n"
            f"• `{p}delenemy` - حذف از لیست دشمنان\n"
            f"• `{p}enemylist` - مشاهده لیست دشمنان\n\n"
            f"🛠 **ابزارهای عمومی:**\n"
            f"• `{p}purge [تعداد]` - پاکسازی سریع پیام‌ها\n"
            f"• `{p}info` - اطلاعات کاربر ریپلای شده\n"
            f"• `{p}save` - ذخیره رسانه محدود/یکبار مصرف در Saved Messages\n"
            f"• `{p}calc [فرمول]` - ماشین حساب سریع ریاضی\n"
            f"• `{p}tagall [متن]` - تگ کردن اعضای گروه\n"
            f"• `{p}ping` - وضعیت و سرعت سلف"
        )
        await message.edit_text(text)

    # Purge messages
    @app.on_message(filters.me & filters.command(["purge", "پاکسازی"], prefixes=prefix))
    async def cmd_purge(client: Client, message: Message):
        db.increment_stat("commands_run")
        count = 10
        if len(message.command) > 1 and message.command[1].isdigit():
            count = min(int(message.command[1]), 100)

        msg_ids = []
        async for m in client.get_chat_history(message.chat.id, limit=count + 1):
            msg_ids.append(m.id)

        if msg_ids:
            await client.delete_messages(message.chat.id, msg_ids)

    # User / Chat Info
    @app.on_message(filters.me & filters.command(["info", "اطلاعات"], prefixes=prefix))
    async def cmd_info(client: Client, message: Message):
        db.increment_stat("commands_run")
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        if not target:
            await message.edit_text("❌ اطلاعات کاربر در دسترس نیست.")
            return

        text = (
            f"👤 **اطلاعات کاربر:**\n\n"
            f"• نام: **{target.first_name}** {target.last_name or ''}\n"
            f"• آیدی عددی: `{target.id}`\n"
            f"• یوزرنیم: @{target.username if target.username else 'ندارد'}\n"
            f"• وضعیت دی‌سی: DC {target.dc_id or 'نامشخص'}\n"
            f"• ربات: {'بله' if target.is_bot else 'خیر'}\n"
            f"• پرمیوم تلگرام: {'بله 🌟' if target.is_premium else 'خیر'}"
        )
        await message.edit_text(text)

    # Math calculator
    @app.on_message(filters.me & filters.command(["calc", "حساب"], prefixes=prefix))
    async def cmd_calc(client: Client, message: Message):
        if len(message.command) < 2:
            await message.edit_text(f"⚠️ نحوه استفاده: `{prefix}calc 25 * 4 + 10`")
            return

        expr = " ".join(message.command[1:])
        # Safe character filter
        allowed = set("0123456789+-*/(). %")
        if not set(expr).issubset(allowed):
            await message.edit_text("❌ عبارت حاوی کاراکترهای غیرمجاز است.")
            return

        try:
            res = eval(expr, {"__builtins__": None}, {})
            await message.edit_text(f"🧮 **محاسبه ریاضی:**\n\n`{expr}` = **{res}**")
        except Exception as e:
            await message.edit_text(f"❌ خطا در محاسبه: `{e}`")

    # Tag all members in group
    @app.on_message(filters.me & filters.command(["tagall", "تگ"], prefixes=prefix))
    async def cmd_tagall(client: Client, message: Message):
        if message.chat.type not in ["group", "supergroup"]:
            await message.edit_text("❌ این دستور فقط در سوپرگروه‌ها کاربرد دارد.")
            return

        custom_text = " ".join(message.command[1:]) if len(message.command) > 1 else "سلام دوستان!"
        await message.delete()

        mentions = []
        async for member in client.get_chat_members(message.chat.id):
            if member.user.is_bot or member.user.is_deleted:
                continue
            name = member.user.first_name or "کاربر"
            mentions.append(f"[{name}](tg://user?id={member.user.id})")

            if len(mentions) >= 5:
                chunk_text = f"📢 {custom_text}\n" + " • ".join(mentions)
                await client.send_message(message.chat.id, chunk_text)
                mentions = []
                await asyncio.sleep(1.5)

        if mentions:
            chunk_text = f"📢 {custom_text}\n" + " • ".join(mentions)
            await client.send_message(message.chat.id, chunk_text)

    # Save restricted / disappearing media to Saved Messages
    @app.on_message(filters.me & filters.command(["save", "ذخیره"], prefixes=prefix))
    async def cmd_save(client: Client, message: Message):
        if not message.reply_to_message:
            await message.edit_text("⚠️ روی مدیای مورد نظر (عکس، فیلم، صوت) ریپلای کنید.")
            return

        replied = message.reply_to_message
        await message.edit_text("⏳ در حال انتقال به پیام‌های ذخیره شده...")
        try:
            await replied.copy("me")
            await message.edit_text("✅ مدیا با موفقیت در Saved Messages ذخیره شد!")
        except Exception as e:
            await message.edit_text(f"❌ خطا در ذخیره مدیا: `{e}`")
