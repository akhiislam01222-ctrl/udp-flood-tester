# handlers/settings.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, MAX_THREADS, DEFAULT_DURATION

def register(app):
    
    @app.on_callback_query(filters.regex("^settings$"))
    async def settings_cb(client, cb: CallbackQuery):
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("❌ Owner only", show_alert=True)
        
        text = (
            f"**⚙️ SETTINGS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"├── Max Threads: `{MAX_THREADS}`\n"
            f"├── Default Duration: `{DEFAULT_DURATION}s`\n"
            f"└── Require Approval: `✅`"
        )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)