# database.py
import json
import os
from datetime import datetime, timedelta
from config import DATA_DIR

def load(name):
    path = f"{DATA_DIR}/{name}.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

def save(name, data):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===== USERS =====
def add_user(user_id, days=7):
    users = load("users")
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    users[str(user_id)] = {
        "user_id": user_id,
        "approved_at": datetime.now().isoformat(),
        "expires_at": expiry,
        "days": days,
        "attacks": 0
    }
    save("users", users)

def get_user(user_id):
    return load("users").get(str(user_id))

def is_active(user_id):
    u = get_user(user_id)
    if not u:
        return False
    return datetime.fromisoformat(u["expires_at"]) > datetime.now()

def all_users():
    return load("users")

def remove_user(user_id):
    users = load("users")
    users.pop(str(user_id), None)
    save("users", users)

def extend_user(user_id, extra_days):
    users = load("users")
    u = users.get(str(user_id))
    if not u:
        return False
    old = datetime.fromisoformat(u["expires_at"])
    u["expires_at"] = (old + timedelta(days=extra_days)).isoformat()
    u["days"] = u.get("days", 0) + extra_days
    save("users", users)
    return True

# ===== ADMINS =====
def add_admin(user_id):
    admins = load("admins")
    admins[str(user_id)] = {"added_at": datetime.now().isoformat()}
    save("admins", admins)

def is_admin(user_id):
    return str(user_id) in load("admins")

def all_admins():
    return load("admins")

def remove_admin(user_id):
    admins = load("admins")
    admins.pop(str(user_id), None)
    save("admins", admins)

# ===== PENDING =====
def add_pending(user_id, username):
    pending = load("pending")
    pending[str(user_id)] = {
        "user_id": user_id,
        "username": username,
        "time": datetime.now().isoformat()
    }
    save("pending", pending)

def approve_pending(user_id, days):
    pending = load("pending")
    if str(user_id) not in pending:
        return False
    del pending[str(user_id)]
    save("pending", pending)
    add_user(user_id, days)
    return True

def reject_pending(user_id):
    pending = load("pending")
    if str(user_id) not in pending:
        return False
    del pending[str(user_id)]
    save("pending", pending)
    return True

def all_pending():
    return load("pending")

# ===== ATTACKS =====
def add_attack(attack_id, data):
    attacks = load("attacks")
    attacks[attack_id] = data
    save("attacks", attacks)

def get_user_attacks(user_id):
    attacks = load("attacks")
    return {k: v for k, v in attacks.items() if v.get("user_id") == user_id}

def all_attacks():
    return load("attacks")

# ===== CONFIG =====
def get_github_config():
    from config import GITHUB_TOKEN, GITHUB_REPO, WORKFLOW_COUNT
    cfg = load("config")
    return cfg.get("github", {
        "token": GITHUB_TOKEN,
        "repo": GITHUB_REPO,
        "count": WORKFLOW_COUNT
    })

def save_github_config(token, repo, count):
    cfg = load("config")
    cfg["github"] = {"token": token, "repo": repo, "count": count}
    save("config", cfg)

# ===== LOGS =====
def add_log(action, user_id, details=""):
    logs = load("logs")
    log_id = f"{int(datetime.now().timestamp() * 1000)}"
    logs[log_id] = {
        "action": action,
        "user_id": user_id,
        "details": details,
        "time": datetime.now().isoformat()
    }
    if len(logs) > 500:
        sorted_logs = sorted(logs.items(), key=lambda x: x[1]["time"])
        logs = dict(sorted_logs[-500:])
    save("logs", logs)

def get_logs(limit=50):
    logs = load("logs")
    sorted_logs = sorted(logs.items(), key=lambda x: x[1]["time"], reverse=True)
    return dict(sorted_logs[:limit])