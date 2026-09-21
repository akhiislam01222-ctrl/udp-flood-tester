# handlers/check.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin
from utils.validators import check_ip_alive, valid_ip
import state
import asyncio

def register(app):

    @app.on_callback_query(filters.regex("^check_ip$"))
    async def check_ip_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)

        state.attack_state[user_id] = {"step": "check_ip"}
        await cb.message.edit_text(
            "**🔍 IP CHECK**\n\n"
            "Send IP address to check:\n"
            "Example: `1.1.1.1`\n\n"
            "/cancel to cancel"
        )

    @app.on_message(filters.private & filters.text &
                    ~filters.command(["start", "cancel"]))
    async def check_ip_input(client, message: Message):
        user_id = message.from_user.id
        if user_id not in state.attack_state:
            return
        s = state.attack_state[user_id]
        if s.get("step") != "check_ip":
            return

        ip = message.text.strip()
        if not valid_ip(ip):
            return await message.reply("❌ **Invalid IP**, try again:")

        state.attack_state.pop(user_id, None)

        msg = await message.reply(
            f"**🔍 Checking `{ip}`...**\n⏳ Please wait..."
        )

        loop = asyncio.get_event_loop()
        alive = await loop.run_in_executor(None, check_ip_alive, ip)

        if alive is True:
            status = "🟢 **LIVE** — Server is UP"
        elif alive is False:
            status = "🔴 **OFFLINE** — Server is DOWN"
        else:
            status = "⚪ **UNKNOWN** — Could not determine"

        await msg.edit_text(
            f"**🔍 IP CHECK RESULT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🌐 IP:** `{ip}`\n"
            f"**📊 Status:** {status}\n"
            f"━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Check Another", callback_data="check_ip"),
                 InlineKeyboardButton("🎯 Attack This", callback_data="launch")],
                [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
            ])
        )
