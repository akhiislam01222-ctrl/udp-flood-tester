# config.py
import os

# ===== TELEGRAM =====
API_ID = 1234567
API_HASH = "your_api_hash_here"
BOT_TOKEN = "your_bot_token_here"
OWNER_ID = 8007254305

# ===== GITHUB =====
GITHUB_TOKEN = "ghp_your_token_here"
GITHUB_REPO = "yourname/my-bot"
WORKFLOW_COUNT = 15

# ===== SERVER =====
PORT = 8080

# ===== PATHS =====
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ===== LIMITS =====
MAX_THREADS = 5000
DEFAULT_THREADS = 1000
MAX_DURATION = 21000
DEFAULT_DURATION = 300

# ===== VALIDATION =====
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise Exception("❌ Missing Telegram credentials!")

if not OWNER_ID:
    raise Exception("❌ OWNER_ID not set!")

if not GITHUB_TOKEN or not GITHUB_REPO:
    print("⚠️ GitHub credentials missing")