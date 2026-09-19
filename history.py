# handlers/history.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, load

PAGE_SIZE = 5

def register(app):
    
    @app.on_callback_query(filters.regex("^history$"))
    async def history_cb(client, cb: CallbackQuery):
        user_id = cb.from_user.id
        if not (user_id == OWNER_ID or is_admin(user_id) or is_active(user_id)):
            return await cb.answer("❌ No access", show_alert=True)
        await show_history(cb, user_id, 0)
    
    @app.on_callback_query(filters.regex("^hist_page_"))
    async def hist_page(client, cb: CallbackQuery):
        page = int(cb.data.split("_")[2])
        await show_history(cb, cb.from_user.id, page)
    
    @app.on_callback_query(filters.regex("^hist_detail_"))
    async def hist_detail(client, cb: CallbackQuery):
        aid = cb.data.replace("hist_detail_", "")
        a = load("attacks").get(aid)
        if not a:
            return await cb.answer("Not found", show_alert=True)
        
        text = (
            f"**📜 DETAILS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🆔** `{aid}`\n"
            f"**🌐** `{a['ip']}:{a['port']}`\n"
            f"**⚡** {a.get('method', 'UDP')}\n"
            f"**⏰** `{a['duration']}s`\n"
            f"**🖥️** `{a['servers']}`\n"
            f"**✅** {a.get('status', 'unknown')}\n"
            f"**📅** `{a['started_at'][:19]}`"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="history")]
        ])
        await cb.message.edit_text(text, reply_markup=kb)

async def show_history(cb, user_id, page):
    attacks = load("attacks")
    
    if user_id == OWNER_ID or is_admin(user_id):
        user_attacks = attacks
    else:
        user_attacks = {k: v for k, v in attacks.items()
                       if v.get("user_id") == user_id}
    
    sorted_items = sorted(user_attacks.items(),
                         key=lambda x: x[1].get("started_at", ""),
                         reverse=True)
    
    total = len(sorted_items)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    
    start = page * PAGE_SIZE
    items = sorted_items[start:start + PAGE_SIZE]
    
    text = (
        f"**📜 HISTORY**\n"
        f"**Total:** `{total}` | **Page:** `{page+1}/{total_pages}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if not items:
        text += "_No attacks_"
    
    buttons = []
    for i, (aid, a) in enumerate(items, start=start+1):
        icon = "🟢" if a.get("status") == "running" else \
               "✅" if a.get("status") == "completed" else \
               "🔴" if a.get("status") == "stopped" else "⚪"
        text += f"**{i}.** {icon} `{a['ip']}:{a['port']}`\n"
        buttons.append([InlineKeyboardButton(
            f"{icon} {a['ip']}:{a['port']}",
            callback_data=f"hist_detail_{aid}"
        )])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀", callback_data=f"hist_page_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶", callback_data=f"hist_page_{page+1}"))
    if nav:
        buttons.append(nav)
    
    buttons.append([InlineKeyboardButton("🏠 Main", callback_data="main_menu")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))