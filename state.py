# state.py — shared global state
import time

# Bot global state
current_target = {
    "ip": None,
    "port": None,
    "threads": 1000,
    "duration": 0,
    "started_at": 0  # unix timestamp
}
watchdog_enabled = False

# Per-user conversation states
attack_state = {}
token_state  = {}
user_state   = {}

def clear_user_state(user_id):
    attack_state.pop(user_id, None)
    token_state.pop(user_id, None)
    user_state.pop(user_id, None)
