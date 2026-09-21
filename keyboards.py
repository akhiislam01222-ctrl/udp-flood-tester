# keyboards.py
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                             ReplyKeyboardMarkup, KeyboardButton,
                             ReplyKeyboardRemove)

# ===== INLINE KEYBOARDS =====

def main_menu(is_admin=False, is_owner=False):
    buttons = [
        [InlineKeyboardButton("🎯 Launch Attack", callback_data="launch"),
         InlineKeyboardButton("📊 Status",        callback_data="status")],
        [InlineKeyboardButton("🛑 Stop Attack",   callback_data="stop"),
         InlineKeyboardButton("📜 History",       callback_data="history")],
        [InlineKeyboardButton("🔍 Check IP",      callback_data="check_ip"),
         InlineKeyboardButton("👤 Profile",       callback_data="profile")],
        [InlineKeyboardButton("🎁 Referral",      callback_data="referral"),
         InlineKeyboardButton("📈 Statistics",    callback_data="stats")],
    ]
    if is_admin or is_owner:
        buttons.append([
            InlineKeyboardButton("👥 Users",    callback_data="users"),
            InlineKeyboardButton("📋 Logs",     callback_data="logs"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ])
    if is_owner:
        buttons.append([
            InlineKeyboardButton("👑 Owner Panel",      callback_data="owner"),
            InlineKeyboardButton("🔑 Token Management", callback_data="token"),
        ])
    return InlineKeyboardMarkup(buttons)

def back_button(target="main_menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=target)]
    ])

def attack_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Attack", callback_data="confirm_attack")],
        [InlineKeyboardButton("❌ Cancel",         callback_data="cancel_attack")]
    ])

def duration_select():
    """Duration inline buttons — click করে select করা যাবে"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("30s",   callback_data="dur_30"),
            InlineKeyboardButton("60s",   callback_data="dur_60"),
            InlineKeyboardButton("120s",  callback_data="dur_120"),
        ],
        [
            InlineKeyboardButton("300s",  callback_data="dur_300"),
            InlineKeyboardButton("600s",  callback_data="dur_600"),
            InlineKeyboardButton("1200s", callback_data="dur_1200"),
        ],
        [
            InlineKeyboardButton("1800s", callback_data="dur_1800"),
            InlineKeyboardButton("3600s", callback_data="dur_3600"),
            InlineKeyboardButton("✏️ Custom", callback_data="dur_custom"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")]
    ])

def method_select():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ UDP FLOOD",  callback_data="method_udp")],
        [InlineKeyboardButton("🔥 TCP FLOOD",  callback_data="method_tcp")],
        [InlineKeyboardButton("🌐 HTTP FLOOD", callback_data="method_http")],
        [InlineKeyboardButton("🐌 SLOWLORIS",  callback_data="method_slow")],
        [InlineKeyboardButton("❌ Cancel",      callback_data="cancel_attack")]
    ])

def stop_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 Stop Attack", callback_data="confirm_stop")],
        [InlineKeyboardButton("🏠 Main Menu",   callback_data="main_menu")]
    ])

# ===== REPLY KEYBOARDS (normal keyboard) =====

def reply_main_menu(is_admin=False, is_owner=False):
    """Bottom normal keyboard"""
    buttons = [
        [KeyboardButton("🎯 Launch Attack"), KeyboardButton("📊 Status")],
        [KeyboardButton("🛑 Stop"),          KeyboardButton("📜 History")],
        [KeyboardButton("🔍 Check IP"),      KeyboardButton("👤 Profile")],
    ]
    if is_admin or is_owner:
        buttons.append([KeyboardButton("👥 Users"), KeyboardButton("📋 Logs")])
    if is_owner:
        buttons.append([KeyboardButton("👑 Owner"), KeyboardButton("🔑 Token")])

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def remove_keyboard():
    return ReplyKeyboardRemove()
