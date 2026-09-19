# handlers/stop.py
from pyrogram import filters
from pyrogram.types import CallbackQuery
from config import OWNER_ID
from database import is_active, is_admin, load, save, add_log
from services.github import cancel_all
from keyboards import stop_confirm, main_menu
from datetime import datetime

import main as main_module

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
        
        if not running:
            return await cb.answer("❌ No running attack", show_alert=True)
        
        aid, a = running
        await cb.message.edit_text(
            f"**🛑 STOP ATTACK**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**⚠️ Sure?**\n\n"
            f"**🎯** `{a['ip']}:{a['port']}`",
            reply_markup=stop_confirm()
        )
    
    @app.on_callback_query(filters.regex("^confirm_stop$"))
    async def confirm_stop(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        
        main_module.watchdog_enabled = False
        main_module.current_target = {"ip": None, "port": None, "threads": 1000}
        
        cancelled = cancel_all()
        
        attacks = load("attacks")
        for aid, a in attacks.items():
            if a.get("user_id") == user_id and a.get("status") == "running":
                a["status"] = "stopped"
                a["stopped_at"] = datetime.now().isoformat()
                add_log("attack_stopped", user_id, f"{a['ip']}:{a['port']}")
                break
        save("attacks", attacks)
        
        await cb.message.edit_text(
            f"**🛑 STOPPED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🖥️ Cancelled:** `{cancelled}`",
            reply_markup=main_menu()
        )