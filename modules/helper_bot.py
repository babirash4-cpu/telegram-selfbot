import asyncio
from typing import Optional
try:
    from pyrogram import Client, filters
    from pyrogram.types import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        CallbackQuery,
        Message
    )
except ImportError:
    Client = None
    filters = None
    InlineKeyboardButton = lambda text, callback_data=None: {"text": text, "callback_data": callback_data}
    InlineKeyboardMarkup = lambda inline_keyboard: {"inline_keyboard": inline_keyboard}
    CallbackQuery = None
    Message = None
from config import Config
from database import db
from modules.tools import get_uptime
from modules.clock import format_time

def get_main_panel_keyboard() -> InlineKeyboardMarkup:
    ad = db.get_anti_delete()
    sec = db.get_secretary()
    clk = db.get_clock()

    ad_icon = "🟢" if ad.get("enabled", True) else "🔴"
    sec_icon = "🟢" if sec.get("enabled", False) or sec.get("afk", False) else "🔴"
    clk_icon = "🟢" if clk.get("enabled", False) else "🔴"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🛡️ آنتی‌دلیت: {ad_icon}", callback_data="toggle_antidelete"),
            InlineKeyboardButton(f"🤖 منشی / AFK: {sec_icon}", callback_data="toggle_secretary")
        ],
        [
            InlineKeyboardButton(f"⏰ ساعت بیو: {clk_icon}", callback_data="toggle_clock"),
            InlineKeyboardButton("🎰 کازینو و شرط‌بندی", callback_data="panel_casino")
        ],
        [
            InlineKeyboardButton("⚔️ مدیریت انمی‌ها (دشمن)", callback_data="panel_enemies"),
            InlineKeyboardButton("💬 پاسخ‌های سریع", callback_data="panel_triggers")
        ],
        [
            InlineKeyboardButton("📊 آمار و وضعیت آنلاین", callback_data="panel_stats"),
            InlineKeyboardButton("🔄 بروزرسانی پنل", callback_data="panel_refresh")
        ]
    ])

def register_helper_bot_handlers(bot: Client):
    owner_filter = filters.user(Config.OWNER_ID)

    @bot.on_message(filters.command(["start", "panel"]) & owner_filter)
    async def cmd_start_panel(client: Client, message: Message):
        stats = db.get_stats()
        text = (
            f"👑 **پنل مدیریت اختصاصی سلف بات تک کاربره**\n\n"
            f"👤 کاربر گرامی، به مرکز کنترل سلف بات خوش آمدید.\n"
            f"⏱ آپ‌تایم سلف: **{get_uptime()}**\n"
            f"⚡ دستورات اجرا شده: **{stats.get('commands_run', 0)}**\n"
            f"☁️ هاست: **Railway.com** (نسخه اختصاصی، بدون تبلیغات و محدودیت)\n\n"
            f"لطفاً بخش مورد نظر خود را از دکمه‌های زیر انتخاب کنید:"
        )
        await message.reply_text(text, reply_markup=get_main_panel_keyboard())

    @bot.on_message(~owner_filter)
    async def ignore_non_owners(client: Client, message: Message):
        await message.reply_text("⛔ این ربات یک پنل کنترل شخصی و تک‌کاربره است و فقط به مالک خود پاسخ می‌دهد.")

    # Callbacks
    @bot.on_callback_query(owner_filter)
    async def handle_panel_callbacks(client: Client, query: CallbackQuery):
        data = query.data

        if data == "panel_refresh" or data == "panel_home":
            await query.edit_message_text(
                f"👑 **پنل مدیریت اختصاصی سلف بات تک کاربره**\n\n"
                f"⏱ آپ‌تایم سلف: **{get_uptime()}**\n"
                f"⚡ دستورات اجرا شده: **{db.get_stats().get('commands_run', 0)}**\n"
                f"🛡️ پیام‌های رهگیری شده: **{db.get_stats().get('anti_delete_caught', 0)}**\n\n"
                f"وضعیت‌ها بروزرسانی شدند:",
                reply_markup=get_main_panel_keyboard()
            )
            await query.answer("پنل بروزرسانی شد! 🔄")

        elif data == "toggle_antidelete":
            ad = db.get_anti_delete()
            new_val = not ad.get("enabled", True)
            db.update_anti_delete(enabled=new_val)
            await query.answer("وضعیت آنتی‌دلیت تغییر کرد!")
            await query.edit_message_reply_markup(reply_markup=get_main_panel_keyboard())

        elif data == "toggle_secretary":
            sec = db.get_secretary()
            new_val = not (sec.get("enabled", False) or sec.get("afk", False))
            db.update_secretary(enabled=new_val, afk=False)
            await query.answer("وضعیت منشی تغییر کرد!")
            await query.edit_message_reply_markup(reply_markup=get_main_panel_keyboard())

        elif data == "toggle_clock":
            clk = db.get_clock()
            new_val = not clk.get("enabled", False)
            db.update_clock(enabled=new_val)
            await query.answer("وضعیت ساعت تغییر کرد!")
            await query.edit_message_reply_markup(reply_markup=get_main_panel_keyboard())

        elif data == "panel_casino":
            c = db.get_casino()
            stats = c.get("stats", {})
            text = (
                f"🎰 **تنظیمات و آمار کازینو و شرط‌بندی:**\n\n"
                f"💰 موجودی: **{c.get('balance', 0):,} سکه**\n"
                f"🛡️ سقف هر شرط: **{c.get('max_bet', 1000):,} سکه**\n"
                f"🛑 حد ضرر خودکار: **{c.get('stop_loss', 500):,} سکه**\n\n"
                f"🏆 تعداد بردها: **{stats.get('wins', 0)}**\n"
                f"💔 تعداد باخت‌ها: **{stats.get('losses', 0)}**\n"
                f"💵 سود کل: **+{stats.get('total_won', 0):,} سکه**\n"
                f"💸 ضرر کل: **-{stats.get('total_lost', 0):,} سکه**"
            )
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ شارژ ۵,۰۰۰ سکه", callback_data="add_balance_5000"),
                    InlineKeyboardButton("➕ شارژ ۱۰,۰۰۰ سکه", callback_data="add_balance_10000")
                ],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="panel_home")]
            ])
            await query.edit_message_text(text, reply_markup=kb)

        elif data.startswith("add_balance_"):
            amount = int(data.replace("add_balance_", ""))
            c = db.get_casino()
            db.update_casino(balance=c.get("balance", 0) + amount)
            await query.answer(f"{amount:,} سکه به موجودی اضافه شد! 💰")
            # Return to casino panel
            c = db.get_casino()
            stats = c.get("stats", {})
            text = (
                f"🎰 **تنظیمات و آمار کازینو و شرط‌بندی:**\n\n"
                f"💰 موجودی جدید: **{c.get('balance', 0):,} سکه**\n"
                f"🛡️ سقف هر شرط: **{c.get('max_bet', 1000):,} سکه**\n"
                f"🛑 حد ضرر خودکار: **{c.get('stop_loss', 500):,} سکه**\n\n"
                f"🏆 تعداد بردها: **{stats.get('wins', 0)}**\n"
                f"💔 تعداد باخت‌ها: **{stats.get('losses', 0)}**"
            )
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ شارژ ۵,۰۰۰ سکه", callback_data="add_balance_5000"),
                    InlineKeyboardButton("➕ شارژ ۱۰,۰۰۰ سکه", callback_data="add_balance_10000")
                ],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="panel_home")]
            ])
            await query.edit_message_text(text, reply_markup=kb)

        elif data == "panel_enemies":
            enemies = db.get_enemies()
            count = len(enemies)
            lines = [f"⚔️ **مدیریت سیستم انمی (دشمنان):**\n", f"تعداد افراد هدف: **{count} نفر**\n"]
            if enemies:
                for uid, d in list(enemies.items())[:10]:
                    lines.append(f"• `{uid}` | حالت: `{d.get('mode', 'text')}`")
            else:
                lines.append("🕊️ در حال حاضر هیچ شخصی در لیست انمی وجود ندارد.")

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧹 پاکسازی کل لیست انمی", callback_data="clear_enemies")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="panel_home")]
            ])
            await query.edit_message_text("\n".join(lines), reply_markup=kb)

        elif data == "clear_enemies":
            for uid in list(db.get_enemies().keys()):
                db.remove_enemy(int(uid))
            await query.answer("کل لیست انمی پاک شد! 🕊️")
            await query.edit_message_text(
                "⚔️ **لیست دشمنان پاکسازی شد.** صلح و صفا برقرار است!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="panel_home")]])
            )

        elif data == "panel_stats":
            stats = db.get_stats()
            clk = db.get_clock()
            curr_clk = format_time(clk.get("font_style", "bold"))
            text = (
                f"📊 **آمار جامع سلف بات تک کاربره:**\n\n"
                f"⏱ زمان فعالیت: **{get_uptime()}**\n"
                f"⚡ تعداد فرامین اجرا شده: **{stats.get('commands_run', 0)}**\n"
                f"🛡️ پیام‌های شکار شده آنتی‌دلیت: **{stats.get('anti_delete_caught', 0)}**\n"
                f"⏰ ساعت فعلی سلف: **{curr_clk}**\n"
                f"🎰 موجودی کازینو: **{db.get_casino().get('balance', 0):,} سکه**\n"
                f"⚔️ افراد در لیست انمی: **{len(db.get_enemies())} نفر**\n"
                f"💬 پاسخ‌های خودکار: **{len(db.get_triggers())} مورد**\n\n"
                f"☁️ پلتفرم: **Railway PaaS (Container)**\n"
                f"🚀 مصرف رم: **حدود ۳۰ تا ۳۵ مگابایت (فوق سبک)**"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="panel_home")]])
            await query.edit_message_text(text, reply_markup=kb)
