# handlers/callbacks.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from config import OWNER_ID
from database import is_admin, approve_pending, reject_pending, add_log, load, save
from keyboards import reply_main_menu
import state

def register(app):

    # ===== /cancel =====
    @app.on_message(filters.command("cancel") & filters.private)
    async def cancel_cmd(client, message: Message):
        uid = message.from_user.id
        had = bool(
            state.attack_state.pop(uid, None) or
            state.token_state.pop(uid, None) or
            state.user_state.pop(uid, None)
        )
        await message.reply(
            "❌ **Cancelled.**" if had else "ℹ️ Nothing to cancel.",
            reply_markup=reply_main_menu(
                is_admin=is_admin(uid),
                is_owner=uid == OWNER_ID
            )
        )

    # ===== Reply Keyboard button handlers =====
    # Normal keyboard button text → callback data map
    REPLY_MAP = {
        "🎯 Launch Attack": "launch",
        "📊 Status":        "status",
        "🛑 Stop":          "stop",
        "📜 History":       "history",
        "🔍 Check IP":      "check_ip",
        "👤 Profile":       "profile",
        "🎁 Referral":      "referral",
        "📈 Statistics":    "stats",
        "👥 Users":         "users",
        "📋 Logs":          "logs",
        "⚙️ Settings":      "settings",
        "👑 Owner":         "owner",
        "🔑 Token":         "token",
    }

    @app.on_message(filters.private & filters.text &
                    ~filters.command(["start", "cancel"]))
    async def reply_kb_handler(client, message: Message):
        uid  = message.from_user.id
        text = message.text.strip()

        # শুধু reply keyboard buttons handle করো
        # attack_state/token_state/user_state এ থাকলে skip (অন্য handler নেবে)
        if uid in state.attack_state or uid in state.token_state or uid in state.user_state:
            return

        action = REPLY_MAP.get(text)
        if not action:
            return  # unknown text - ignore

        # Fake callback এর মতো করে handle করি
        # send করব inline menu as new message
        from keyboards import main_menu as inline_menu
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        action_map = {
            "launch":   ("🎯 Launch Attack",  None),
            "status":   ("📊 Status",          None),
            "stop":     ("🛑 Stop Attack",     None),
            "history":  ("📜 History",          None),
            "check_ip": ("🔍 Check IP",         None),
            "profile":  ("👤 Profile",          None),
            "referral": ("🎁 Referral",         None),
            "stats":    ("📈 Statistics",       None),
            "users":    ("👥 Users",            None),
            "logs":     ("📋 Logs",             None),
            "settings": ("⚙️ Settings",        None),
            "owner":    ("👑 Owner Panel",      None),
            "token":    ("🔑 Token Management", None),
        }

        label = action_map.get(action, (text, None))[0]
        await message.reply(
            f"**{label}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(label, callback_data=action)]
            ])
        )

    # ===== Main Menu callback =====
    @app.on_callback_query(filters.regex("^main_menu$"))
    async def main_menu_cb(client, cb: CallbackQuery):
        uid = cb.from_user.id
        state.clear_user_state(uid)
        await cb.message.edit_text(
            f"**🏠 Main Menu**\n**🆔 ID:** `{uid}`",
            reply_markup=None
        )
        await client.send_message(
            uid,
            "**👇 Use keyboard below:**",
            reply_markup=reply_main_menu(
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
            return await cb.answer("❌ Not in pending", show_alert=True)

        add_log("user_approved", user_id, f"{days}d")

        refs = load("referrals")
        ref  = refs.get(str(user_id))
        if ref and not ref.get("active"):
            ref["active"] = True
            save("referrals", refs)
            try:
                await client.send_message(
                    ref["referrer_id"],
                    f"**🎁 Referral Bonus!**\nYour referral `{user_id}` approved!"
                )
            except Exception:
                pass

        await cb.message.edit_text(f"**✅ Approved** — `{user_id}` — `{days}d`")
        try:
            await client.send_message(
                user_id,
                f"**✅ Access Granted — {days} days**\n\nSend /start",
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
            await client.send_message(user_id, "**❌ Access Denied.**")
        except Exception:
            pass

    @app.on_callback_query(filters.regex("^noop$"))
    async def noop(client, cb: CallbackQuery):
        await cb.answer()
