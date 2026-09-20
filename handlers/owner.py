# handlers/owner.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, WORKFLOW_COUNT
from database import all_users, all_pending, load
from datetime import datetime

def register(app):
    
    @app.on_callback_query(filters.regex("^owner$"))
    async def owner_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        users = all_users()
        pending = all_pending()
        admins = load("admins")
        attacks = load("attacks")
        today = datetime.now().date().isoformat()
        today_attacks = sum(1 for a in attacks.values()
                          if a.get("started_at", "").startswith(today))
        
        text = (
            f"**👑 OWNER PANEL**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"├── Users: `{len(users)}`\n"
            f"├── Admins: `{len(admins)}`\n"
            f"├── Pending: `{len(pending)}`\n"
            f"├── Workflows: `{WORKFLOW_COUNT}`\n"
            f"└── Today: `{today_attacks}` attacks"
        )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Users", callback_data="users"),
             InlineKeyboardButton("🎫 Pending", callback_data="u_pending")],
            [InlineKeyboardButton("👑 Admins", callback_data="u_admins"),
             InlineKeyboardButton("🔑 Token", callback_data="token")],
            [InlineKeyboardButton("📋 Logs", callback_data="logs"),
             InlineKeyboardButton("📈 Stats", callback_data="stats")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)