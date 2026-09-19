# handlers/token.py
from pyrogram import filters
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)
from config import OWNER_ID
from database import get_github_config, save_github_config, add_log
from services.github import test_connection

token_state = {}

def register(app):
    
    @app.on_callback_query(filters.regex("^token$"))
    async def token_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        cfg = get_github_config()
        token = cfg.get("token", "")
        masked = f"{token[:10]}...{token[-4:]}" if len(token) > 14 else "Not set"
        
        text = (
            f"**🔑 TOKEN MANAGEMENT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"├── Repo: `{cfg.get('repo', 'N/A')}`\n"
            f"├── Token: `{masked}`\n"
            f"└── Count: `{cfg.get('count', 15)}`"
        )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Token", callback_data="t_token"),
             InlineKeyboardButton("📦 Repo", callback_data="t_repo")],
            [InlineKeyboardButton("⚙️ Count", callback_data="t_count"),
             InlineKeyboardButton("🔄 Test", callback_data="t_test")],
            [InlineKeyboardButton("📊 Rate Limit", callback_data="t_rate")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)
    
    @app.on_callback_query(filters.regex("^t_(token|repo|count)$"))
    async def change_item(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        key = cb.data.replace("t_", "")
        token_state[cb.from_user.id] = key
        
        labels = {
            "token": "GitHub Token",
            "repo": "Repo (user/repo)",
            "count": "Workflow Count"
        }
        await cb.message.edit_text(
            f"**🔧 Change {labels[key]}**\n\n"
            f"Send new value:\n"
            f"⚠️ Message will be deleted\n\n"
            f"/cancel to cancel"
        )
    
    @app.on_callback_query(filters.regex("^t_test$"))
    async def test_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        ok = test_connection()
        await cb.answer("✅ OK" if ok else "❌ Failed", show_alert=True)
    
    @app.on_callback_query(filters.regex("^t_rate$"))
    async def rate_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        import requests
        cfg = get_github_config()
        try:
            r = requests.get("https://api.github.com/rate_limit",
                           headers={"Authorization": f"Bearer {cfg['token']}"},
                           timeout=10).json()
            core = r["resources"]["core"]
            text = (
                f"**📊 RATE LIMIT**\n"
                f"**Limit:** `{core['limit']}`\n"
                f"**Remaining:** `{core['remaining']}`"
            )
        except:
            text = "❌ Failed"
        
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="token")]
        ]))
    
    @app.on_message(filters.private & filters.text &
                    filters.user(OWNER_ID) &
                    ~filters.command(["start", "cancel"]))
    async def token_input(client, message: Message):
        uid = message.from_user.id
        if uid not in token_state:
            return
        
        key = token_state.pop(uid)
        value = message.text.strip()
        
        if value == "/cancel":
            return await message.reply("❌ Cancelled")
        
        cfg = get_github_config()
        if key == "token":
            cfg["token"] = value
        elif key == "repo":
            cfg["repo"] = value
        elif key == "count":
            try:
                cfg["count"] = int(value)
            except:
                return await message.reply("❌ Invalid")
        
        save_github_config(cfg["token"], cfg["repo"], cfg["count"])
        add_log("token_changed", uid, key)
        
        try:
            await message.delete()
        except:
            pass
        
        await message.reply(
            f"**✅ Updated:** `{key}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="token")]
            ])
        )