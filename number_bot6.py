# --- Part 7: Admin Panel Main Dashboard ---
def render_admin_panel(chat_id, user_id, message_id=None):
    """Renders the main admin console UI"""
    users = read_json("users.json")
    numbers = read_json("numbers.json")
    files = read_json("files.json")
    
    available = len([n for n in numbers if not n.get("used")])
    total = len(numbers) or 1
    
    # Progress Bar Logic
    perc = int((available / total) * 10)
    bar = "█" * perc + "░" * (10 - perc)
    
    text = (
        f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>DXA BOT ADMIN PANEL</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{e('📊', PREMIUM_EMOJIS['GRAPH'])} <b>OVERVIEW</b>\n"
        f"  {e('👤', PREMIUM_EMOJIS['USER'])} Total Users: <b>{len(users)}</b>\n"
        f"  {e('🔢', PREMIUM_EMOJIS['NUMBERS'])} Total Stock: <b>{len(numbers)}</b>\n"
        f"  {e('🚀', PREMIUM_EMOJIS['ROCKET'])} Active Stock: <b>{available}</b>\n\n"
        f"<b>Inventory Health:</b>\n"
        f"[{bar}] {available} Free\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"📤 {e(' ', PREMIUM_EMOJIS['UPLOAD'])} Upload", callback_data="admin_upload"),
        types.InlineKeyboardButton(f"🗑 {e(' ', PREMIUM_EMOJIS['DELETE'])} Files", callback_data="admin_files")
    )
    markup.row(
        types.InlineKeyboardButton(f"📢 {e(' ', PREMIUM_EMOJIS['BROADCAST'])} Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton(f"⚙️ {e(' ', PREMIUM_EMOJIS['SETTINGS'])} Settings", callback_data="admin_settings")
    )
    markup.row(
        types.InlineKeyboardButton("📋 View Used", callback_data="admin_view_used"),
        types.InlineKeyboardButton("🗑 Clear Unused", callback_data="admin_clear_unused")
    )
    markup.add(types.InlineKeyboardButton(f"🔙 {e(' ', PREMIUM_EMOJIS['CLOSE'])} Close Menu", callback_data="close_admin"))
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        last_menus[user_id] = sent.message_id
