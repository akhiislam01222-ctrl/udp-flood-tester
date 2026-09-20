# keyboards.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_admin=False, is_owner=False):
    buttons = [
        [InlineKeyboardButton("🎯 Launch Attack", callback_data="launch"),
         InlineKeyboardButton("📊 Check Status", callback_data="status")],
        [InlineKeyboardButton("🛑 Stop Attack", callback_data="stop"),
         InlineKeyboardButton("📜 Attack History", callback_data="history")],
        [InlineKeyboardButton("🎁 Referral System", callback_data="referral"),
         InlineKeyboardButton("👤 My Profile", callback_data="profile")],
        [InlineKeyboardButton("👥 User Management", callback_data="users"),
         InlineKeyboardButton("⚙️ Bot Settings", callback_data="settings")],
        [InlineKeyboardButton("📈 Statistics", callback_data="stats"),
         InlineKeyboardButton("📋 Activity Logs", callback_data="logs")],
        [InlineKeyboardButton("👑 Owner Panel", callback_data="owner"),
         InlineKeyboardButton("🔑 Token Management", callback_data="token")]
    ]
    return InlineKeyboardMarkup(buttons)

def back_button(target="main_menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=target)]
    ])

def attack_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_attack")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")]
    ])

def method_select():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ UDP FLOOD", callback_data="method_udp")],
        [InlineKeyboardButton("🔥 TCP FLOOD", callback_data="method_tcp")],
        [InlineKeyboardButton("🌐 HTTP FLOOD", callback_data="method_http")],
        [InlineKeyboardButton("🐌 SLOWLORIS", callback_data="method_slow")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]
    ])

def stop_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 Yes, Stop", callback_data="confirm_stop")],
        [InlineKeyboardButton("❌ Cancel", callback_data="main_menu")]
    ])
