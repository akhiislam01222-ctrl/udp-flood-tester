# handlers/callbacks.py
from pyrogram import filters
from pyrogram.types import CallbackQuery
from config import OWNER_ID
from database import is_admin, approve_pending, reject_pending, add_log
from keyboards import main_menu

def register(app):
    
    @app.on_callback_query(filters.regex("^main_menu$"))
    async def main_menu_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        await cb.message.edit_text(
            f"**🏠 Main Menu**\n\n**🆔 ID:** `{user_id}`",
            reply_markup=main_menu(
                is_admin=is_admin(user_id),
                is_owner=user_id == OWNER_ID
            )
        )
    
    @app.on_callback_query(filters.regex("^approve_"))
    async def approve_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        parts = cb.data.split("_")
        user_id = int(parts[1])
        days = int(parts[2])
        
        if approve_pending(user_id, days):
            add_log("user_approved", user_id, f"{days} days")
            await cb.message.edit_text(
                f"**✅ Approved**\n`{user_id}` — `{days}d`"
            )
            try:
                await client.send_message(user_id,
                    f"**✅ Access Granted!**\n**⏰** `{days} days`\n\n/start")
            except:
                pass
        else:
            await cb.answer("❌ Not pending", show_alert=True)
    
    @app.on_callback_query(filters.regex("^reject_"))
    async def reject_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        user_id = int(cb.data.split("_")[1])
        reject_pending(user_id)
        add_log("user_rejected", user_id)
        await cb.message.edit_text(f"**❌ Rejected**\n`{user_id}`")
    
    @app.on_callback_query(filters.regex("^noop$"))
    async def noop(client, cb: CallbackQuery):
        await cb.answer()