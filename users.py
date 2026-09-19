# handlers/users.py
from pyrogram import filters
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)
from config import OWNER_ID
from database import (is_admin, add_user, all_users, all_pending,
                     approve_pending, reject_pending, add_log,
                     add_admin, load)
from datetime import datetime

user_state = {}

def register(app):
    
    @app.on_callback_query(filters.regex("^users$"))
    async def users_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID and not is_admin(cb.from_user.id):
            return await cb.answer("❌ Admin only", show_alert=True)
        
        users = all_users()
        pending = all_pending()
        admins = load("admins")
        
        text = (
            f"**👥 USER MANAGEMENT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"├── Users: `{len(users)}`\n"
            f"├── Admins: `{len(admins)}`\n"
            f"└── Pending: `{len(pending)}`"
        )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add User", callback_data="u_add"),
             InlineKeyboardButton("📋 View All", callback_data="u_view")],
            [InlineKeyboardButton(f"⏳ Pending ({len(pending)})", callback_data="u_pending"),
             InlineKeyboardButton("👑 Admins", callback_data="u_admins")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)
    
    @app.on_callback_query(filters.regex("^u_add$"))
    async def add_start(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        user_state[cb.from_user.id] = {"action": "add_user_id"}
        await cb.message.edit_text(
            f"**➕ ADD USER - STEP 1/2**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Send user ID:**\n"
            f"**Example:** `123456789`"
        )
    
    @app.on_callback_query(filters.regex("^u_view$"))
    async def view_all(client, cb: CallbackQuery):
        users = all_users()
        if not users:
            return await cb.answer("No users", show_alert=True)
        
        text = "**👥 USERS**\n━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, u) in enumerate(list(users.items())[:20], 1):
            exp = datetime.fromisoformat(u["expires_at"])
            days = (exp - datetime.now()).days
            icon = "🟢" if days > 0 else "🔴"
            text += f"{i}. {icon} `{uid}` — `{days}d`\n"
        
        await cb.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="users")]
            ])
        )
    
    @app.on_callback_query(filters.regex("^u_pending$"))
    async def view_pending(client, cb: CallbackQuery):
        pending = all_pending()
        if not pending:
            return await cb.answer("No pending", show_alert=True)
        
        text = "**⏳ PENDING**\n━━━━━━━━━━━━━━━━━━━━━\n"
        buttons = []
        for i, (uid, p) in enumerate(pending.items(), 1):
            text += f"{i}. 👤 `{uid}` — @{p.get('username', 'None')}\n"
            buttons.append([
                InlineKeyboardButton(f"✅ 7d", callback_data=f"approve_{uid}_7"),
                InlineKeyboardButton(f"✅ 30d", callback_data=f"approve_{uid}_30"),
                InlineKeyboardButton(f"❌", callback_data=f"reject_{uid}")
            ])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="users")])
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    
    @app.on_callback_query(filters.regex("^u_admins$"))
    async def view_admins(client, cb: CallbackQuery):
        admins = load("admins")
        text = f"**👑 ADMINS**\n━━━━━━━━━━━━━━━━━━━━━\n**👑 Owner:** `{OWNER_ID}`\n\n"
        for i, uid in enumerate(admins.keys(), 1):
            text += f"{i}. 👑 `{uid}`\n"
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Admin", callback_data="u_add_admin")],
            [InlineKeyboardButton("🔙 Back", callback_data="users")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)
    
    @app.on_callback_query(filters.regex("^u_add_admin$"))
    async def add_admin_start(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        user_state[cb.from_user.id] = {"action": "add_admin"}
        await cb.message.edit_text("**Send admin user ID:**")
    
    @app.on_message(filters.private & filters.text &
                    filters.user(OWNER_ID) &
                    ~filters.command(["start", "cancel"]))
    async def users_input(client, message: Message):
        uid = message.from_user.id
        if uid not in user_state:
            return
        
        state = user_state[uid]
        action = state["action"]
        text = message.text.strip()
        
        if text == "/cancel":
            del user_state[uid]
            return await message.reply("❌ Cancelled")
        
        if action == "add_user_id":
            try:
                new_id = int(text)
            except:
                return await message.reply("❌ Invalid ID")
            state["user_id"] = new_id
            state["action"] = "add_user_days"
            return await message.reply(
                f"**✅ User:** `{new_id}`\n\n"
                f"**Send duration (days):**"
            )
        
        if action == "add_user_days":
            try:
                days = int(text)
            except:
                return await message.reply("❌ Invalid number")
            
            add_user(state["user_id"], days)
            add_log("user_added", state["user_id"], f"{days} days")
            new_id = state["user_id"]
            del user_state[uid]
            
            try:
                await client.send_message(new_id,
                    f"**✅ Access Granted!**\n**⏰** `{days} days`")
            except:
                pass
            
            return await message.reply(f"**✅ Added:** `{new_id}` — `{days}d`")
        
        if action == "add_admin":
            try:
                new_id = int(text)
            except:
                return await message.reply("❌ Invalid ID")
            add_admin(new_id)
            add_log("admin_added", new_id)
            del user_state[uid]
            return await message.reply(f"**✅ Admin added:** `{new_id}`")