# handlers/token.py
from pyrogram import filters
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)
from config import OWNER_ID
from database import get_github_config, save_github_config, add_log
from services.github import test_connection, get_rate_limit
import state

def register(app):

    @app.on_callback_query(filters.regex("^token$"))
    async def token_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)

        cfg = get_github_config()
        t = cfg.get("token", "")
        masked = f"{t[:10]}...{t[-4:]}" if len(t) > 14 else ("Not set" if not t else t)

        text = (
            f"**🔑 TOKEN MANAGEMENT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Repo:** `{cfg.get('repo', 'N/A')}`\n"
            f"**Token:** `{masked}`\n"
            f"**Count:** `{cfg.get('count', 15)}`"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Set Token", callback_data="t_token"),
             InlineKeyboardButton("📦 Set Repo", callback_data="t_repo")],
            [InlineKeyboardButton("⚙️ Set Count", callback_data="t_count"),
             InlineKeyboardButton("🔄 Test Conn", callback_data="t_test")],
            [InlineKeyboardButton("📊 Rate Limit", callback_data="t_rate")],
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)

    @app.on_callback_query(filters.regex("^t_(token|repo|count)$"))
    async def change_item(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        key = cb.data.replace("t_", "")
        state.token_state[cb.from_user.id] = key
        labels = {
            "token": "GitHub Personal Access Token\n(starts with `ghp_` or `github_pat_`)",
            "repo": "GitHub Repo\n(format: `username/repo-name`)",
            "count": "Workflow Count\n(1 to 15)"
        }
        await cb.message.edit_text(
            f"**🔧 Set {key.upper()}**\n\n"
            f"**Send:** {labels[key]}\n\n"
            f"/cancel to cancel"
        )

    @app.on_callback_query(filters.regex("^t_test$"))
    async def test_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        await cb.answer("⏳ Testing...", show_alert=False)
        ok = test_connection()
        await cb.answer("✅ Connected!" if ok else "❌ Connection Failed!", show_alert=True)

    @app.on_callback_query(filters.regex("^t_rate$"))
    async def rate_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        data = get_rate_limit()
        if data and "resources" in data:
            core = data["resources"]["core"]
            text = (
                f"**📊 RATE LIMIT**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**Core:**\n"
                f"├── Limit: `{core.get('limit', 'N/A')}`\n"
                f"├── Used: `{core.get('used', 'N/A')}`\n"
                f"└── Remaining: `{core.get('remaining', 'N/A')}`"
            )
        else:
            text = "**❌ Failed to fetch rate limit**\n\nCheck your token."
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="token")]
        ]))

    @app.on_message(filters.private & filters.text &
                    filters.user(OWNER_ID) &
                    ~filters.command(["start", "cancel"]))
    async def token_input(client, message: Message):
        uid = message.from_user.id
        if uid not in state.token_state:
            return
        key = state.token_state.pop(uid)
        value = message.text.strip()

        cfg = get_github_config()
        if key == "token":
            if not (value.startswith("ghp_") or value.startswith("github_pat_")):
                await message.reply(
                    "⚠️ **Warning:** Token format unexpected.\n"
                    "Expected `ghp_...` or `github_pat_...`\n"
                    "Saved anyway — test connection to verify."
                )
            cfg["token"] = value
        elif key == "repo":
            if "/" not in value or len(value.split("/")) != 2:
                return await message.reply(
                    "❌ **Invalid format!**\n"
                    "Use: `username/repo-name`"
                )
            cfg["repo"] = value
        elif key == "count":
            try:
                c = int(value)
                if not (1 <= c <= 15):
                    return await message.reply("❌ Count must be **1 to 15**")
                cfg["count"] = c
            except ValueError:
                return await message.reply("❌ Invalid number")

        save_github_config(cfg.get("token", ""), cfg.get("repo", ""), cfg.get("count", 15))
        add_log("token_changed", uid, key)

        try:
            await message.delete()
        except Exception:
            pass

        await message.reply(
            f"**✅ {key.upper()} updated successfully**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Token", callback_data="token")]
            ])
        )
