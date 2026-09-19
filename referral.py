# handlers/referral.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import load

def register(app):
    
    @app.on_callback_query(filters.regex("^referral$"))
    async def referral_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        refs = load("referrals")
        my_refs = [r for r in refs.values() if r.get("referrer_id") == user_id]
        
        bot_username = (await client.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        
        text = (
            f"**🎁 REFERRAL**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🔗 Your Link:**\n"
            f"`{ref_link}`\n\n"
            f"**📊 Stats:**\n"
            f"├── Total: `{len(my_refs)}`\n"
            f"├── Active: `{sum(1 for r in my_refs if r.get('active'))}`\n"
            f"└── Bonus: `{len(my_refs) * 3}` days"
        )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Share Link",
                                 url=f"https://t.me/share/url?url={ref_link}")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)