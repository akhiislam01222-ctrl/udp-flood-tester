# handlers/callbacks.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from config import OWNER_ID
from database import is_admin, approve_pending, reject_pending, add_log, load, save
from keyboards import main_menu
import state

def register(app):

    # ===== /cancel — সব pending state clear করে =====
    @app.on_message(filters.command("cancel") & filters.private)
    async def cancel_cmd(client, message: Message):
        uid = message.from_user.id
        had_state = bool(
            state.attack_state.pop(uid, None) or
            state.token_state.pop(uid, None) or
            state.user_state.pop(uid, None)
        )
        if had_state:
            await message.reply("❌ **Cancelled.**")
        else:
            await message.reply("ℹ️ Nothing to cancel.")

    # ===== Main Menu =====
    @app.on_callback_query(filters.regex("^main_menu$"))
    async def main_menu_cb(client, cb: CallbackQuery):
        uid = cb.from_user.id
        # কোনো pending state থাকলে সেটাও clear করো
        state.clear_user_state(uid)
        await cb.message.edit_text(
            f"**🏠 MAIN MENU**\n\n**🆔 ID:** `{uid}`",
            reply_markup=main_menu(
                is_admin=is_admin(uid),
                is_owner=uid == OWNER_ID
            )
        )

    # ===== Approve =====
    @app.on_callback_query(filters.regex(r"^approve_\d+_\d+$"))
    async def approve_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        parts = cb.data.split("_")
        try:
            user_id = int(parts[1])
            days    = int(parts[2])
        except (IndexError, ValueError):
            return await cb.answer("❌ Invalid data", show_alert=True)

        if not approve_pending(user_id, days):
            return await cb.answer("❌ User not in pending list", show_alert=True)

        add_log("user_approved", user_id, f"{days}d")

        # referral activate
        refs = load("referrals")
        ref  = refs.get(str(user_id))
        if ref and not ref.get("active"):
            ref["active"] = True
            save("referrals", refs)
            try:
                await client.send_message(
                    ref["referrer_id"],
                    f"**🎁 Referral Bonus!**\n"
                    f"Your referral `{user_id}` was approved!\n"
                    f"**+3 bonus days** will be credited."
                )
            except Exception:
                pass

        await cb.message.edit_text(
            f"**✅ Approved**\n`{user_id}` — `{days} days`"
        )
        try:
            await client.send_message(
                user_id,
                f"**✅ Access Granted — {days} days**\n\nUse /start"
            )
        except Exception:
            pass

    # ===== Reject =====
    @app.on_callback_query(filters.regex(r"^reject_\d+$"))
    async def reject_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        try:
            user_id = int(cb.data.split("_")[1])
        except (IndexError, ValueError):
            return await cb.answer("❌ Invalid data", show_alert=True)

        reject_pending(user_id)
        add_log("user_rejected", user_id)
        await cb.message.edit_text(f"**❌ Rejected** — `{user_id}`")
        try:
            await client.send_message(user_id,
                "**❌ Access Denied.**\nYour request was rejected.")
        except Exception:
            pass

    # ===== No-op (dummy button) =====
    @app.on_callback_query(filters.regex("^noop$"))
    async def noop(client, cb: CallbackQuery):
        await cb.answer()
