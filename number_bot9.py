# --- Part 10: Admin - OTP Group System ---
def render_manage_otp_groups(chat_id, user_id, message_id):
    """UI for managing where OTPs are forwarded and custom group buttons"""
    s = get_settings()
    groups = s.get("otp_groups", [])
    
    text = (
        f"{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>OTP GROUP CONTROL</b>\n"
        f"OTPs will be forwarded to these groups.\n\n"
        f"<b>Active Groups:</b>\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    
    for gid in groups:
        text += f"• <code>{gid}</code>\n"
        markup.row(
            types.InlineKeyboardButton(f"🛠 Buttons for {gid}", callback_data=f"setup_grp_btns_{gid}"),
            types.InlineKeyboardButton(f"🗑 Remove", callback_data=f"del_group_{gid}")
        )
        
    if not groups: text += "<i>No groups connected.</i>\n"
    
    markup.row(
        types.InlineKeyboardButton("➕ Add Group (ID)", callback_data="add_group_prompt"),
        types.InlineKeyboardButton("➕ Global Button", callback_data="add_global_btn_prompt")
    )
    markup.add(types.InlineKeyboardButton("🔙 Back to Settings", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
