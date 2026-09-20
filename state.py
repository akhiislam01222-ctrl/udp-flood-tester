# state.py — shared global state
# Bot global state
current_target = {"ip": None, "port": None, "threads": 1000, "duration": 0}
watchdog_enabled = False

# Per-user conversation states (message handlers)
attack_state = {}   # launch.py uses this
token_state = {}    # token.py uses this
user_state = {}     # users.py uses this

def clear_user_state(user_id):
    """User এর সব pending state clear করো"""
    attack_state.pop(user_id, None)
    token_state.pop(user_id, None)
    user_state.pop(user_id, None)
