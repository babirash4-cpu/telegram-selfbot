import asyncio
import random
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

# Game emojis
EMOJI_DICE = "🎲"
EMOJI_DART = "🎯"
EMOJI_BASKET = "🏀"
EMOJI_FOOTBALL = "⚽"
EMOJI_SLOT = "🎰"
EMOJI_BOWLING = "🎳"

# Tic Tac Toe boards: chat_id -> state
ttt_games: Dict[int, Dict] = {}

def get_emoji_result_text(emoji: str, value: int) -> str:
    if emoji == EMOJI_DICE:
        return f"عدد تاس: {value} 🎲"
    elif emoji == EMOJI_DART:
        return f"امتیاز دارت: {value} 🎯" + (" (وسط خال! 🎯🔥)" if value >= 5 else "")
    elif emoji == EMOJI_BASKET:
        return "گل شد! 🏀🔥" if value in [4, 5] else "خطا رفت! ❌"
    elif emoji == EMOJI_FOOTBALL:
        return "گل شد! ⚽🔥" if value in [3, 4, 5] else "خطا رفت! ❌"
    elif emoji == EMOJI_SLOT:
        return f"امتیاز اسلات ماشین: {value} 🎰" + (" (جک‌پات! 🏆💰)" if value in [1, 64, 22, 43] else "")
    elif emoji == EMOJI_BOWLING:
        return f"تعداد پین‌های افتاده: {value} 🎳" + (" (استرایک! 💥)" if value == 6 else "")
    return f"نتیجه: {value}"

async def roll_game(client: Client, message: Message, emoji: str, bet: int = 0):
    await message.delete()
    sent_dice = await client.send_dice(message.chat.id, emoji=emoji)
    val = sent_dice.dice.value

    # Process betting calculation if bet specified
    if bet > 0:
        casino_conf = db.get_casino()
        max_bet = casino_conf.get("max_bet", 1000)
        current_bal = casino_conf.get("balance", 10000)

        if bet > max_bet:
            await client.send_message(
                message.chat.id,
                f"⚠️ شرط {bet} بالاتر از سقف مجاز ({max_bet}) است! با سقف شرط‌بندی اجرا شد.",
                reply_to_message_id=sent_dice.id
            )
            bet = max_bet

        if bet > current_bal:
            await client.send_message(
                message.chat.id,
                f"❌ موجودی کافی نیست! موجودی فعلی شما: {current_bal} سکه",
                reply_to_message_id=sent_dice.id
            )
            return

        won = False
        multiplier = 1.0

        if emoji == EMOJI_DICE:
            won = val >= 4
            multiplier = 1.8 if val in [4, 5] else 2.5
        elif emoji in [EMOJI_BASKET, EMOJI_FOOTBALL]:
            won = val in [4, 5] or (emoji == EMOJI_FOOTBALL and val in [3, 4, 5])
            multiplier = 2.0
        elif emoji == EMOJI_DART:
            won = val >= 4
            multiplier = 2.0 if val == 4 else 3.5
        elif emoji == EMOJI_SLOT:
            won = val in [1, 22, 43, 64]
            multiplier = 5.0

        win_amount = int(bet * multiplier) if won else bet
        db.record_bet(won, win_amount)
        new_bal = db.get_casino()["balance"]

        res_text = get_emoji_result_text(emoji, val)
        status_text = f"🎉 **برنده شدی!** (+{win_amount} سکه)" if won else f"💔 **باختی!** (-{bet} سکه)"

        await asyncio.sleep(2.5)  # Wait for dice animation to complete
        await client.send_message(
            message.chat.id,
            f"🎰 **نتیجه بازی کازینو:**\n\n"
            f"🕹 نوع بازی: {emoji}\n"
            f"📊 {res_text}\n"
            f"{status_text}\n"
            f"💰 موجودی فعلی: **{new_bal:,} سکه**",
            reply_to_message_id=sent_dice.id
        )

def register_casino_handlers(app: Client):
    prefix = Config.PREFIX

    # Magic dice commands
    @app.on_message(filters.me & filters.command(["dice", "تاس"], prefixes=prefix))
    async def cmd_dice(client: Client, message: Message):
        db.increment_stat("commands_run")
        bet = 0
        if len(message.command) > 1 and message.command[1].isdigit():
            bet = int(message.command[1])
        await roll_game(client, message, EMOJI_DICE, bet)

    @app.on_message(filters.me & filters.command(["dart", "دارت"], prefixes=prefix))
    async def cmd_dart(client: Client, message: Message):
        db.increment_stat("commands_run")
        bet = 0
        if len(message.command) > 1 and message.command[1].isdigit():
            bet = int(message.command[1])
        await roll_game(client, message, EMOJI_DART, bet)

    @app.on_message(filters.me & filters.command(["basket", "بسکتبال"], prefixes=prefix))
    async def cmd_basket(client: Client, message: Message):
        db.increment_stat("commands_run")
        bet = 0
        if len(message.command) > 1 and message.command[1].isdigit():
            bet = int(message.command[1])
        await roll_game(client, message, EMOJI_BASKET, bet)

    @app.on_message(filters.me & filters.command(["football", "فوتبال"], prefixes=prefix))
    async def cmd_football(client: Client, message: Message):
        db.increment_stat("commands_run")
        bet = 0
        if len(message.command) > 1 and message.command[1].isdigit():
            bet = int(message.command[1])
        await roll_game(client, message, EMOJI_FOOTBALL, bet)

    @app.on_message(filters.me & filters.command(["slot", "اسلات"], prefixes=prefix))
    async def cmd_slot(client: Client, message: Message):
        db.increment_stat("commands_run")
        bet = 0
        if len(message.command) > 1 and message.command[1].isdigit():
            bet = int(message.command[1])
        await roll_game(client, message, EMOJI_SLOT, bet)

    @app.on_message(filters.me & filters.command(["bowling", "بولینگ"], prefixes=prefix))
    async def cmd_bowling(client: Client, message: Message):
        db.increment_stat("commands_run")
        bet = 0
        if len(message.command) > 1 and message.command[1].isdigit():
            bet = int(message.command[1])
        await roll_game(client, message, EMOJI_BOWLING, bet)

    # Casino balance and stats
    @app.on_message(filters.me & filters.command(["balance", "موجودی", "کازینو"], prefixes=prefix))
    async def cmd_balance(client: Client, message: Message):
        db.increment_stat("commands_run")
        c = db.get_casino()
        stats = c.get("stats", {})
        total_games = stats.get("wins", 0) + stats.get("losses", 0)
        win_rate = (stats.get("wins", 0) / total_games * 100) if total_games > 0 else 0

        text = (
            f"🎰 **پنل آمار کازینو و شرط‌بندی:**\n\n"
            f"💰 موجودی: **{c.get('balance', 0):,} سکه**\n"
            f"🛡️ سقف هر شرط: **{c.get('max_bet', 1000):,} سکه**\n"
            f"🛑 حد ضرر خودکار (Stop Loss): **{c.get('stop_loss', 500):,} سکه**\n\n"
            f"📈 تعداد کل بازی‌ها: **{total_games}**\n"
            f"🏆 بردها: **{stats.get('wins', 0)}** ({win_rate:.1f}%)\n"
            f"💔 باخت‌ها: **{stats.get('losses', 0)}**\n"
            f"💵 کل سود کسب شده: **+{stats.get('total_won', 0):,} سکه**\n"
            f"💸 کل ضرر: **-{stats.get('total_lost', 0):,} سکه**\n\n"
            f"💡 برای شرط بستن دستور را با مقدار اجرا کنید:\n"
            f"`{prefix}dice 100` یا `{prefix}dart 200`"
        )
        await message.edit_text(text)

    # Reset balance or set balance
    @app.on_message(filters.me & filters.command(["setbalance", "شارژ"], prefixes=prefix))
    async def cmd_set_balance(client: Client, message: Message):
        if len(message.command) > 1 and message.command[1].isdigit():
            new_val = int(message.command[1])
            db.update_casino(balance=new_val)
            await message.edit_text(f"✅ موجودی کازینو با موفقیت روی **{new_val:,}** سکه تنظیم شد.")
        else:
            await message.edit_text(f"⚠️ نحوه استفاده: `{prefix}setbalance 5000`")
