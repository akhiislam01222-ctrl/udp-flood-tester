# handlers/status.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, load
from services.github import get_all_runs
from datetime import datetime
import state

def register(app):

    @app.on_callback_query(filters.regex("^status$"))
    async def status_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)

        attacks = load("attacks")
        running = None

        # Owner/Admin — যেকোনো running attack দেখবে
        if user_id == OWNER_ID or is_admin(user_id):
            for aid, a in attacks.items():
                if a.get("status") == "running":
                    running = (aid, a)
                    break
        else:
            # Normal user — শুধু নিজেরটা
            for aid, a in attacks.items():
                if a.get("user_id") == user_id and a.get("status") == "running":
                    running = (aid, a)
                    break

        if running:
            aid, a = running
            try:
                started = datetime.fromisoformat(a["started_at"])
                elapsed = int((datetime.now() - started).total_seconds())
            except (KeyError, ValueError):
                elapsed = 0

            try:
                runs = get_all_runs()
                active = sum(
                    1 for wf, s in runs.items()
                    if wf.startswith("bot") and s in ["in_progress", "queued"]
                )
            except Exception:
                active = "?"

            duration = a.get("duration", "?")
            servers  = a.get("servers", "?")

            text = (
                f"**📊 ATTACK STATUS**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 **RUNNING**\n\n"
                f"**🆔 ID:** `{aid}`\n"
                f"**🎯 Target:** `{a.get('ip','?')}:{a.get('port','?')}`\n"
                f"**⚡ Method:** `{a.get('method','UDP FLOOD')}`\n"
                f"**⏰ Elapsed:** `{elapsed}s / {duration}s`\n"
                f"**🖥️ Servers:** `{active}/{servers}`\n"
                f"**👤 By:** `{a.get('user_id','?')}`"
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="status"),
                 InlineKeyboardButton("🛑 Stop", callback_data="stop")],
                [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
            ])
        else:
            # Watchdog state থেকেও check করি
            if state.current_target["ip"]:
                text = (
                    f"**📊 ATTACK STATUS**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🟡 **WATCHDOG ACTIVE**\n\n"
                    f"**🎯 Target:** `{state.current_target['ip']}:{state.current_target['port']}`\n"
                    f"**👁️ Watchdog:** {'🟢 ON' if state.watchdog_enabled else '🔴 OFF'}"
                )
            else:
                text = (
                    f"**📊 ATTACK STATUS**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔴 **IDLE**\n\n"
                    f"**✅ No attack running**"
                )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Launch", callback_data="launch"),
                 InlineKeyboardButton("📜 History", callback_data="history")],
                [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
            ])

        await cb.message.edit_text(text, reply_markup=kb)
