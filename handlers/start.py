# handlers/start.py
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, add_pending, add_log, add_user, load, save
from keyboards import main_menu

def register(app):

    @app.on_message(filters.command("start") & filters.private)
    async def start_cmd(client, message: Message):
        user_id = message.from_user.id
        username = message.from_user.username or "None"

        # Referral check
        args = message.command[1] if len(message.command) > 1 else ""
        referrer_id = None
        if args.startswith("ref_"):
            try:
                referrer_id = int(args.replace("ref_", ""))
                if referrer_id == user_id:
                    referrer_id = None  # নিজেকে refer করা যাবে না
            except ValueError:
                referrer_id = None

        # Owner
        if user_id == OWNER_ID:
            return await message.reply_text(
                f"**👑 Welcome Owner!**\n\n"
                f"**🆔 ID:** `{user_id}`\n"
                f"**✅ Full Access**",
                reply_markup=main_menu(is_owner=True)
            )

        # Admin
        if is_admin(user_id):
            return await message.reply_text(
                f"**👑 Welcome Admin!**\n\n"
                f"**🆔 ID:** `{user_id}`",
                reply_markup=main_menu(is_admin=True)
            )

        # Active user
        if is_active(user_id):
            return await message.reply_text(
                f"**✅ Welcome back!**\n\n"
                f"**🆔 ID:** `{user_id}`",
                reply_markup=main_menu()
            )

        # Referral save
        if referrer_id:
            refs = load("referrals")
            if str(user_id) not in refs:
                refs[str(user_id)] = {
                    "referrer_id": referrer_id,
                    "referred_at": __import__("datetime").datetime.now().isoformat(),
                    "active": False
                }
                save("referrals", refs)
                add_log("referral", referrer_id, f"referred {user_id}")

        # Pending request
        add_pending(user_id, username)
        add_log("access_request", user_id)

        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ 7 days", callback_data=f"approve_{user_id}_7"),
                 InlineKeyboardButton("✅ 30 days", callback_data=f"approve_{user_id}_30")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
            ])
            ref_text = f"\n**🎁 Referred by:** `{referrer_id}`" if referrer_id else ""
            await client.send_message(
                OWNER_ID,
                f"**🆕 New Access Request**\n\n"
                f"**👤 ID:** `{user_id}`\n"
                f"**📛 Username:** @{username}"
                f"{ref_text}\n\n"
                f"**Approve?**",
                reply_markup=kb
            )
        except Exception as e:
            print(f"Owner notify failed: {e}")

        await message.reply_text(
            f"**⏳ Access Request Sent**\n\n"
            f"**👤 ID:** `{user_id}`\n"
            f"**📊 Status:** Pending approval\n\n"
            f"_Please wait for owner approval._"
        )
