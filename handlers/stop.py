# handlers/stop.py
from pyrogram import filters
from pyrogram.types import CallbackQuery
from config import OWNER_ID
from database import is_active, is_admin, load, save, add_log
from services.github import cancel_all
from keyboards import stop_confirm, main_menu
from datetime import datetime
import state  # circular import এড়াতে main এর পরিবর্তে state module

def register(app):

    @app.on_callback_query(filters.regex("^stop$"))
    async def stop_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)

        attacks = load("attacks")
        running = None
        for aid, a in attacks.items():
            if a.get("user_id") == user_id and a.get("status") == "running":
                running = (aid, a)
                break

        # Owner/Admin যেকোনো running attack দেখতে পারবে
        if not running and (user_id == OWNER_ID or is_admin(user_id)):
            for aid, a in attacks.items():
                if a.get("status") == "running":
                    running = (aid, a)
                    break

        if not running:
            return await cb.answer("❌ No running attack found", show_alert=True)

        aid, a = running
        await cb.message.edit_text(
            f"**🛑 STOP ATTACK**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**⚠️ Sure you want to stop?**\n\n"
            f"**🎯** `{a['ip']}:{a['port']}`\n"
            f"**⚡** {a.get('method', 'UDP FLOOD')}",
            reply_markup=stop_confirm()
        )

    @app.on_callback_query(filters.regex("^confirm_stop$"))
    async def confirm_stop(client, cb: CallbackQuery):
        user_id = cb.from_user.id

        # State reset
        state.watchdog_enabled = False
        state.current_target = {"ip": None, "port": None, "threads": 1000, "duration": 0}

        cancelled = cancel_all()

        # সব running attack বন্ধ করো
        attacks = load("attacks")
        stopped_count = 0
        for aid, a in attacks.items():
            if a.get("status") == "running":
                a["status"] = "stopped"
                a["stopped_at"] = datetime.now().isoformat()
                add_log("attack_stopped", a.get("user_id", user_id),
                        f"{a['ip']}:{a['port']}")
                stopped_count += 1
        save("attacks", attacks)

        await cb.message.edit_text(
            f"**🛑 STOPPED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🖥️ Workflows Cancelled:** `{cancelled}`\n"
            f"**📊 Attacks Stopped:** `{stopped_count}`",
            reply_markup=main_menu(
                is_admin=is_admin(user_id),
                is_owner=user_id == OWNER_ID
            )
        )
