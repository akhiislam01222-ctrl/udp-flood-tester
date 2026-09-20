# config.py
import os
import base64

# ===== TELEGRAM =====
API_ID    = 30864848
API_HASH  = "47dceaee86036e75a7c3fe39576101db"
BOT_TOKEN = "8911118423:AAGYvL2yRQHj0M9r_zqg7bXBmJRb1Nfc19Y"
OWNER_ID  = 8007254305

# ===== GITHUB =====
# Set GITHUB_TOKEN environment variable in your deployment platform
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO    = "akhiislam01222-ctrl/udp-flood-tester"
WORKFLOW_COUNT = 15

# ===== SERVER =====
PORT = 8080

# ===== PATHS =====
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ===== LIMITS =====
MAX_THREADS      = 50000000
DEFAULT_THREADS  = 10000000000000
MAX_DURATION     = 21000000
DEFAULT_DURATION = 300

# ===== VALIDATION =====
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise Exception("Missing Telegram credentials!")

if not OWNER_ID:
    raise Exception("OWNER_ID not set!")
