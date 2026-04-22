# --- Part 15: Bot Initialization & Main Loop ---
# This part glues all handlers together and starts the bot

@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    if not check_force_join(uid):
        s = get_settings()
        markup = types.InlineKeyboardMarkup()
        for c in s['channels']: markup.add(types.InlineKeyboardButton(f"Join: {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="verify_join"))
        return bot.send_message(uid, f"{e('🚫', PREMIUM_EMOJIS['CLOSE'])} <b>JOIN REQUIRED</b>", reply_markup=markup)
    
    # Register User
    users = read_json("users.json")
    if not any(str(u['uid']) == str(uid) for u in users):
        users.append({"uid": str(uid), "joinedAt": str(datetime.now())})
        write_json("users.json", users)
        
    welcome_text = (
        f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} <b>DXA NUMBER BOT</b> 》═\n"
        f"━━━━━━━━━━━\n"
        f"Welcome <b>{message.from_user.first_name}</b>!\n"
        f"Ready to generate virtual numbers.\n"
        f"━━━━━━━━━━━"
    )
    bot.send_message(uid, welcome_text, reply_markup=get_main_keyboard(uid))

# Start OTP Monitoring Thread
threading.Thread(target=start_otp_monitor, daemon=True).start()

print("Full system mirrored across 15 parts. Bot is ready to start.")

# Start Bot Polling
if __name__ == "__main__":
    bot.infinity_polling()
