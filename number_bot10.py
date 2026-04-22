# --- Part 11: Admin - Branding & Link Settings ---
def render_manage_branding(chat_id, user_id, message_id):
    """UI for custom branding, masking, and support links"""
    s = get_settings()
    
    text = (
        f"{e('🔍', PREMIUM_EMOJIS['NOTE'])} <b>BRANDING & IDENTITY</b>\n"
        f"━━━━━━━━━━━━━\n"
        f"<b>Brand Name:</b> <code>{s['brand_name']}</code>\n"
        f"<b>Mask Text:</b> <code>{s['mask_text']}</code>\n"
        f"<b>OTP Channel Link:</b> {s['otp_link']}\n"
        f"━━━━━━━━━━━━━"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✏️ Edit Brand", callback_data="set_brand_prompt"),
        types.InlineKeyboardButton("✏️ Edit Mask", callback_data="set_mask_prompt")
    )
    markup.add(types.InlineKeyboardButton("✏️ Edit OTP Link", callback_data="set_link_prompt"))
    markup.add(types.InlineKeyboardButton("🔙 Back to Settings", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
