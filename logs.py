# handlers/logs.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_admin, get_logs

def register(app):
    
    @app.on_callback_query(filters.regex("^logs$"))
    async def logs_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ Admin only", show_alert=True)
        
        logs = get_logs(limit=20)
        icons = {
            "attack_started": "🟢", "attack_stopped": "🛑",
            "user_added": "👤", "user_approved": "✅",
            "user_rejected": "❌", "access_request": "📝",
            "token_changed": "🔑", "admin_added": "👑",
            "attack_failed": "🔴",
        }
        
        text = "**📋 ACTIVITY LOGS**\n━━━━━━━━━━━━━━━━━━━━━\n"
        if not logs:
            text += "_No logs_"
        else:
            for log_id, log in logs.items():
                icon = icons.get(log["action"], "⚪")
                t = log["time"][11:19]
                text += f"{icon} `{t}` **{log['action']}** — `{log['user_id']}`"
                if log.get("details"):
                    text += f"\n   _{log['details']}_"
                text += "\n"
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="logs"),
             InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)