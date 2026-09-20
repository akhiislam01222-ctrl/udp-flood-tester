# handlers/statistics.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_admin, load, all_users
from datetime import datetime, timedelta

def register(app):
    
    @app.on_callback_query(filters.regex("^stats$"))
    async def stats_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        attacks = load("attacks")
        my = [a for a in attacks.values() if a.get("user_id") == user_id]
        
        total = len(my)
        success = sum(1 for a in my if a.get("status") in ["completed", "stopped"])
        
        text = (
            f"**📈 STATISTICS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"├── Total: `{total}`\n"
            f"├── Success: `{success}`\n"
            f"└── Failed: `{total - success}`\n\n"
        )
        
        if my:
            text += "**Last 7 Days:**\n"
            for i in range(6, -1, -1):
                day = (datetime.now() - timedelta(days=i)).date().isoformat()
                count = sum(1 for a in my if a.get("started_at", "").startswith(day))
                bar = "▓" * min(count, 10) + "░" * max(0, 10 - count)
                text += f"`{day[-5:]}` {bar} `{count}`\n"
        
        if user_id == OWNER_ID or is_admin(user_id):
            users = all_users()
            text += (
                f"\n**📊 Global:**\n"
                f"├── Users: `{len(users)}`\n"
                f"└── Attacks: `{len(attacks)}`"
            )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="stats"),
             InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)