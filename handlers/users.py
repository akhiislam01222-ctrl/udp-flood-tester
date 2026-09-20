# handlers/users.py
from pyrogram import filters
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)
from config import OWNER_ID
from database import (is_admin, add_user, all_users, all_pending,
                     approve_pending, reject_pending, add_log,
                     add_admin, remove_admin, remove_user, load, save)
from datetime import datetime
import state

def register(app):

    @app.on_callback_query(filters.regex("^users$"))
    async def users_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ Admin only", show_alert=True)
        users  = all_users()
        pending = all_pending()
        admins = load("admins")
        text = (
            f"**👥 USER MANAGEMENT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Active Users:** `{len(users)}`\n"
            f"**Admins:** `{len(admins)}`\n"
            f"**Pending:** `{len(pending)}`"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add User", callback_data="u_add"),
             InlineKeyboardButton("📋 View All", callback_data="u_view")],
            [InlineKeyboardButton(f"⏳ Pending ({len(pending)})", callback_data="u_pending"),
             InlineKeyboardButton("👑 Admins", callback_data="u_admins")],
            [InlineKeyboardButton("➖ Remove User", callback_data="u_remove")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)

    @app.on_callback_query(filters.regex("^u_add$"))
    async def add_start(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        state.user_state[cb.from_user.id] = {"action": "add_id"}
        await cb.message.edit_text(
            "**➕ ADD USER — Step 1/2**\n\n"
            "Send user **Telegram ID** (numbers only):\n\n"
            "/cancel to cancel"
        )

    @app.on_callback_query(filters.regex("^u_remove$"))
    async def remove_start(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        state.user_state[cb.from_user.id] = {"action": "remove_id"}
        await cb.message.edit_text(
            "**➖ REMOVE USER**\n\n"
            "Send user **Telegram ID** to remove:\n\n"
            "/cancel to cancel"
        )

    @app.on_callback_query(filters.regex("^u_view$"))
    async def view_all(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        users = all_users()
        if not users:
            return await cb.answer("No users yet", show_alert=True)
        now = datetime.now()
        text = "**👥 ALL USERS**\n━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, u) in enumerate(list(users.items())[:20], 1):
            try:
                exp = datetime.fromisoformat(u["expires_at"])
                days = (exp - now).days
                icon = "🟢" if days > 0 else "🔴"
                text += f"{i}. {icon} `{uid}` — `{max(0,days)}d`\n"
            except Exception:
                text += f"{i}. ⚠️ `{uid}`\n"
        if len(users) > 20:
            text += f"\n_...and {len(users)-20} more_"
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="users")]
        ]))

    @app.on_callback_query(filters.regex("^u_pending$"))
    async def view_pending(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        pending = all_pending()
        if not pending:
            return await cb.answer("No pending requests", show_alert=True)
        text = "**⏳ PENDING REQUESTS**\n━━━━━━━━━━━━━━━━━━━━━\n"
        buttons = []
        for i, (uid, p) in enumerate(pending.items(), 1):
            text += f"{i}. 👤 `{uid}` — @{p.get('username','None')}\n"
            buttons.append([
                InlineKeyboardButton("✅ 7d",  callback_data=f"approve_{uid}_7"),
                InlineKeyboardButton("✅ 30d", callback_data=f"approve_{uid}_30"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")
            ])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="users")])
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    @app.on_callback_query(filters.regex("^u_admins$"))
    async def view_admins(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ No permission", show_alert=True)
        admins = load("admins")
        text = f"**👑 ADMINS**\n━━━━━━━━━━━━━━━━━━━━━\n**Owner:** `{OWNER_ID}`\n\n"
        if admins:
            for i, uid in enumerate(admins.keys(), 1):
                text += f"{i}. `{uid}`\n"
        else:
            text += "_No admins yet_"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Admin", callback_data="u_add_admin"),
             InlineKeyboardButton("➖ Remove Admin", callback_data="u_rm_admin")],
            [InlineKeyboardButton("🔙 Back", callback_data="users")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)

    @app.on_callback_query(filters.regex("^u_add_admin$"))
    async def add_admin_start(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        state.user_state[cb.from_user.id] = {"action": "add_admin"}
        await cb.message.edit_text(
            "**👑 ADD ADMIN**\n\nSend Telegram user ID:\n\n/cancel to cancel"
        )

    @app.on_callback_query(filters.regex("^u_rm_admin$"))
    async def rm_admin_start(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        state.user_state[cb.from_user.id] = {"action": "rm_admin"}
        await cb.message.edit_text(
            "**👑 REMOVE ADMIN**\n\nSend Telegram user ID:\n\n/cancel to cancel"
        )

    @app.on_message(filters.private & filters.text &
                    filters.user(OWNER_ID) &
                    ~filters.command(["start", "cancel"]))
    async def users_input(client, message: Message):
        uid = message.from_user.id
        if uid not in state.user_state:
            return
        s = state.user_state[uid]
        action = s["action"]
        text = message.text.strip()

        if text.startswith("/"):
            state.user_state.pop(uid, None)
            return await message.reply("❌ Cancelled")

        # --- add_id: get user id first ---
        if action == "add_id":
            try:
                new_id = int(text)
            except ValueError:
                return await message.reply("❌ Invalid ID — numbers only")
            s["uid"] = new_id
            s["action"] = "add_days"
            return await message.reply(
                f"**✅ ID:** `{new_id}`\n\n"
                f"**Step 2/2 — Send duration (days):**\n"
                f"Example: `7` or `30`"
            )

        # --- add_days: get days then save ---
        if action == "add_days":
            try:
                days = int(text)
                if days <= 0:
                    raise ValueError
            except ValueError:
                return await message.reply("❌ Enter a positive number")
            new_id = s["uid"]
            add_user(new_id, days)
            add_log("user_added", new_id, f"{days}d")
            state.user_state.pop(uid, None)
            try:
                await client.send_message(new_id,
                    f"**✅ Access Granted — {days} days**\n\nUse /start")
            except Exception:
                pass
            return await message.reply(
                f"**✅ User `{new_id}` added — {days} days**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 Users", callback_data="users")]
                ])
            )

        # --- remove_id ---
        if action == "remove_id":
            try:
                new_id = int(text)
            except ValueError:
                return await message.reply("❌ Invalid ID")
            remove_user(new_id)
            add_log("user_removed", new_id)
            state.user_state.pop(uid, None)
            return await message.reply(
                f"**✅ User `{new_id}` removed**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 Users", callback_data="users")]
                ])
            )

        # --- add_admin ---
        if action == "add_admin":
            try:
                new_id = int(text)
            except ValueError:
                return await message.reply("❌ Invalid ID")
            add_admin(new_id)
            add_log("admin_added", new_id)
            state.user_state.pop(uid, None)
            return await message.reply(
                f"**✅ Admin `{new_id}` added**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👑 Admins", callback_data="u_admins")]
                ])
            )

        # --- rm_admin ---
        if action == "rm_admin":
            try:
                new_id = int(text)
            except ValueError:
                return await message.reply("❌ Invalid ID")
            remove_admin(new_id)
            add_log("admin_removed", new_id)
            state.user_state.pop(uid, None)
            return await message.reply(
                f"**✅ Admin `{new_id}` removed**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👑 Admins", callback_data="u_admins")]
                ])
            )
