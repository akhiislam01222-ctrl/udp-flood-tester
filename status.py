# handlers/status.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, load
from services.github import get_all_runs
from datetime import datetime

def register(app):
    
    @app.on_callback_query(filters.regex("^status$"))
    async def status_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)
        
        attacks = load("attacks")
        running = None
        for aid, a in attacks.items():
            if a.get("user_id") == user_id and a.get("status") == "running":
                running = (aid, a)
                break
        
        if running:
            aid, a = running
            started = datetime.fromisoformat(a["started_at"])
            elapsed = int((datetime.now() - started).total_seconds())
            runs = get_all_runs()
            active = sum(1 for wf, s in runs.items()
                        if wf.startswith("bot") and s in ["in_progress", "queued"])
            
            text = (
                f"**📊 ATTACK STATUS**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**🟢 RUNNING**\n"
                f"**🆔** `{aid}`\n"
                f"**🎯** `{a['ip']}:{a['port']}`\n"
                f"**⚡** {a.get('method', 'UDP')}\n"
                f"**⏰** `{elapsed}s / {a['duration']}s`\n"
                f"**🖥️ Servers:** `{active}/{a['servers']}`"
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="status"),
                 InlineKeyboardButton("🛑 Stop", callback_data="stop")],
                [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
            ])
            return await cb.message.edit_text(text, reply_markup=kb)
        
        text = (
            f"**📊 ATTACK STATUS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🔴 IDLE**\n"
            f"**✅ Ready**"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Launch", callback_data="launch"),
             InlineKeyboardButton("📜 History", callback_data="history")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)