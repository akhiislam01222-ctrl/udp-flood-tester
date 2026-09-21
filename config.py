# config.py
import os
import base64

# ===== TELEGRAM =====
# Keep credentials out of source control and provide them via deployment secrets.
API_ID    = int(os.getenv("API_ID", "0"))
API_HASH  = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID  = int(os.getenv("OWNER_ID", "0"))

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
