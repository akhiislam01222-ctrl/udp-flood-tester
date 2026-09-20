# handlers/referral.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import load, save
from datetime import datetime

def register(app):

    @app.on_callback_query(filters.regex("^referral$"))
    async def referral_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id

        # referrals DB auto-initialize
        refs = load("referrals")  # returns {} if not exists - OK

        my_refs = [r for r in refs.values() if r.get("referrer_id") == user_id]
        active_refs = [r for r in my_refs if r.get("active", False)]

        me = await client.get_me()
        bot_username = me.username or "unknown"
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

        bonus_days = len(my_refs) * 3  # প্রতি referral = 3 days bonus

        text = (
            f"**🎁 REFERRAL SYSTEM**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🔗 Your Link:**\n"
            f"`{ref_link}`\n\n"
            f"**📊 Stats:**\n"
            f"├── Total Referrals: `{len(my_refs)}`\n"
            f"├── Active: `{len(active_refs)}`\n"
            f"└── Bonus Earned: `{bonus_days} days`"
        )

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link",
                                 url=f"https://t.me/share/url?url={ref_link}&text=Join%20now!")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="referral"),
             InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)
