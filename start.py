# handlers/start.py
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, add_pending, add_log
from keyboards import main_menu

def register(app):
    
    @app.on_message(filters.command("start") & filters.private)
    async def start_cmd(client, message: Message):
        user_id = message.from_user.id
        username = message.from_user.username or "None"
        
        if user_id == OWNER_ID:
            return await message.reply_text(
                f"**👑 Welcome Owner!**\n\n"
                f"**🆔 ID:** `{user_id}`\n"
                f"**✅ Full Access**",
                reply_markup=main_menu(is_owner=True)
            )
        
        if is_admin(user_id):
            return await message.reply_text(
                f"**👑 Welcome Admin!**\n\n"
                f"**🆔 ID:** `{user_id}`",
                reply_markup=main_menu(is_admin=True)
            )
        
        if is_active(user_id):
            return await message.reply_text(
                f"**✅ Welcome back!**\n\n"
                f"**🆔 ID:** `{user_id}`",
                reply_markup=main_menu()
            )
        
        add_pending(user_id, username)
        add_log("access_request", user_id)
        
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ 7 days", callback_data=f"approve_{user_id}_7"),
                 InlineKeyboardButton("✅ 30 days", callback_data=f"approve_{user_id}_30")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
            ])
            await client.send_message(
                OWNER_ID,
                f"**🆕 New Access Request**\n\n"
                f"**👤 ID:** `{user_id}`\n"
                f"**📛 Username:** @{username}\n\n"
                f"**Approve:**",
                reply_markup=kb
            )
        except Exception as e:
            print(f"Notify failed: {e}")
        
        await message.reply_text(
            f"**⏳ Access Request Sent**\n\n"
            f"**👤 ID:** `{user_id}`\n"
            f"**📊 Status:** Pending"
        )