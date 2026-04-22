# --- Part 9: Admin - Co-Admin Management ---
def render_manage_admins(chat_id, user_id, message_id):
    """UI for managing the list of co-admins"""
    s = get_settings()
    admins = s.get("admins", [])
    
    text = (
        f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN MANAGEMENT</b>\n\n"
        f"<b>Master:</b> <code>{ADMIN_ID}</code>\n"
        f"<b>Co-Admins:</b>\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    
    for idx, adm in enumerate(admins):
        text += f"{idx+1}. <code>{adm}</code>\n"
        markup.add(types.InlineKeyboardButton(f"🗑 Demote {adm}", callback_data=f"del_admin_{idx}"))
        
    if not admins: text += "<i>No co-admins.</i>\n"
    
    markup.add(types.InlineKeyboardButton("➕ Add Co-Admin (UID)", callback_data="add_admin_prompt"))
    markup.add(types.InlineKeyboardButton("🔙 Back to Settings", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
