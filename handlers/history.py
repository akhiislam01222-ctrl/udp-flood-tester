# handlers/history.py
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import is_active, is_admin, load

PAGE_SIZE = 5

def register(app):

    @app.on_callback_query(filters.regex("^history$"))
    async def history_cb(client, cb: CallbackQuery):
        uid = cb.from_user.id
        if not (uid == OWNER_ID or is_admin(uid) or is_active(uid)):
            return await cb.answer("❌ No access", show_alert=True)
        await show_history(cb, uid, 0)

    @app.on_callback_query(filters.regex(r"^hist_page_\d+$"))
    async def hist_page(client, cb: CallbackQuery):
        try:
            page = int(cb.data.split("_")[2])
        except (IndexError, ValueError):
            page = 0
        await show_history(cb, cb.from_user.id, page)

    @app.on_callback_query(filters.regex(r"^hist_detail_.+$"))
    async def hist_detail(client, cb: CallbackQuery):
        aid = cb.data.replace("hist_detail_", "")
        attacks = load("attacks")
        a = attacks.get(aid)
        if not a:
            return await cb.answer("❌ Attack not found", show_alert=True)

        icon = ("🟢" if a.get("status") == "running" else
                "🔴" if a.get("status") == "stopped" else
                "✅" if a.get("status") == "completed" else "⚪")

        started = a.get("started_at", "N/A")
        started_fmt = started[:19] if len(started) >= 19 else started

        text = (
            f"**📜 ATTACK DETAIL**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"**🆔 ID:** `{aid}`\n"
            f"**🌐 Target:** `{a.get('ip','?')}:{a.get('port','?')}`\n"
            f"**⚡ Method:** `{a.get('method','UDP FLOOD')}`\n"
            f"**⏰ Duration:** `{a.get('duration','?')}s`\n"
            f"**🖥️ Servers:** `{a.get('servers','?')}`\n"
            f"**📊 Status:** {icon} `{a.get('status','unknown')}`\n"
            f"**👤 User:** `{a.get('user_id','?')}`\n"
            f"**📅 Started:** `{started_fmt}`"
        )
        if a.get("stopped_at"):
            text += f"\n**🛑 Stopped:** `{a['stopped_at'][:19]}`"

        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 History", callback_data="history"),
             InlineKeyboardButton("🏠 Main", callback_data="main_menu")]
        ]))


async def show_history(cb, user_id, page):
    attacks = load("attacks")

    if user_id == OWNER_ID or is_admin(user_id):
        filtered = attacks
    else:
        filtered = {k: v for k, v in attacks.items()
                    if v.get("user_id") == user_id}

    sorted_items = sorted(
        filtered.items(),
        key=lambda x: x[1].get("started_at", ""),
        reverse=True
    )

    total = len(sorted_items)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    items = sorted_items[start:start + PAGE_SIZE]

    text = (
        f"**📜 ATTACK HISTORY**\n"
        f"**Total:** `{total}` | **Page:** `{page+1}/{total_pages}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    )

    buttons = []
    if not items:
        text += "_No attacks yet_"
    else:
        for i, (aid, a) in enumerate(items, start=start+1):
            icon = ("🟢" if a.get("status") == "running" else
                    "🔴" if a.get("status") == "stopped" else
                    "✅" if a.get("status") == "completed" else "⚪")
            ip   = a.get("ip", "?")
            port = a.get("port", "?")
            text += f"**{i}.** {icon} `{ip}:{port}`\n"
            buttons.append([InlineKeyboardButton(
                f"{icon} {ip}:{port}",
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
