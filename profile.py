# handlers/profile.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, get_user, load
from datetime import datetime

def register(app):
    
    @app.on_callback_query(filters.regex("^profile$"))
    async def profile_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        user = cb.from_user
        
        if user_id == OWNER_ID:
            role, expiry, days_left = "👑 Owner", "∞", "∞"
        elif is_admin(user_id):
            role, expiry, days_left = "👑 Admin", "∞", "∞"
        elif is_active(user_id):
            u = get_user(user_id)
            exp = datetime.fromisoformat(u["expires_at"])
            days_left = (exp - datetime.now()).days
            expiry = exp.strftime("%Y-%m-%d")
            role = "👤 User"
        else:
            role, expiry, days_left = "⏳ No Access", "—", "—"
        
        attacks = load("attacks")
        my = [a for a in attacks.values() if a.get("user_id") == user_id]
        total = len(my)
        success = sum(1 for a in my if a.get("status") in ["completed", "stopped"])
        rate = int(success / total * 100) if total else 0
        
        text = (
            f"**👤 PROFILE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🆔** `{user_id}`\n"
            f"**📛** @{user.username or 'None'}\n"
            f"**🎭** {role}\n"
            f"**📅 Expires:** `{expiry}`\n"
            f"**⏰ Days:** `{days_left}`\n\n"
            f"**📊 Stats:**\n"
            f"├── Total: `{total}`\n"
            f"├── Success: `{success}`\n"
            f"└── Rate: `{rate}%`"
        )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="profile"),
             InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)