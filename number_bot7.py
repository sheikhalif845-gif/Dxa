# --- Part 8: Admin - Channel Management (Manage Force Join) ---
def render_manage_force_join(chat_id, user_id, message_id):
    """UI for managing multiple force-join channels"""
    s = get_settings()
    status = "Enabled ✅" if s.get("force_join") else "Disabled ❌"
    
    text = (
        f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} <b>FORCE JOIN SETUP</b>\n"
        f"Status: <b>{status}</b>\n\n"
        f"<b>Current Channels:</b>\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    
    channels = s.get("channels", [])
    for idx, channel in enumerate(channels):
        text += f"{idx+1}. {channel['name']} (<code>{channel['username']}</code>)\n"
        markup.add(types.InlineKeyboardButton(f"🗑 Remove {channel['name']}", callback_data=f"del_channel_{idx}"))
    
    if not channels: text += "<i>No channels added.</i>\n"
    
    markup.row(
        types.InlineKeyboardButton(f"{'OFF 🛑' if s['force_join'] else 'ON ✅'}", callback_data="toggle_force_join"),
        types.InlineKeyboardButton("➕ Add Channel", callback_data="add_channel_prompt")
    )
    markup.add(types.InlineKeyboardButton("🔙 Back to Settings", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
