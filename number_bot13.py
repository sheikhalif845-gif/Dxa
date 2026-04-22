# --- Part 14: User - Number Allocation Flow ---
def handle_service_selection(chat_id, user_id, message_id, service_name):
    """UI for selecting a country after choosing a service"""
    numbers = read_json("numbers.json")
    available_countries = sorted(list(set([n["country"] for n in numbers if not n.get("used") and n["service"] == service_name])))
    
    if not available_countries:
        return bot.answer_callback_query(message_id, "❌ No stock available for this service!", show_alert=True)
        
    text = f"📍 <b>Select Country for {service_name}:</b>"
    markup = types.InlineKeyboardMarkup()
    
    for country in available_countries:
        markup.add(types.InlineKeyboardButton(f"📍 {country}", callback_data=f"buy_cnt_{service_name}_{country}"))
    
    markup.add(types.InlineKeyboardButton("🔙 Back to Services", callback_data="buy_number_start"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

def handle_final_allocation(chat_id, user_id, message_id, service_name, country):
    """Final allocation of numbers to the user"""
    all_numbers = read_json("numbers.json")
    available_stock = [n for n in all_numbers if not n.get("used") and n["service"] == service_name and n["country"] == country]
    
    if len(available_stock) < 3:
        return bot.answer_callback_query(message_id, "❌ Not enough stock! Minimum 3 numbers required.", show_alert=True)
        
    # Allocate 3 numbers
    selected = random.sample(available_stock, 3)
    selected_ids = [n["id"] for n in selected]
    
    for num in all_numbers:
        if num["id"] in selected_ids:
            num["used"] = True
            num["assignedTo"] = user_id
            num["assignedAt"] = str(datetime.now())
            
    write_json("numbers.json", all_numbers)
    
    icons = [e("1️⃣", PREMIUM_EMOJIS["N1"]), e("2️⃣", PREMIUM_EMOJIS["N2"]), e("3️⃣", PREMIUM_EMOJIS["N3"])]
    num_list = ""
    for i, n in enumerate(selected):
        num_str = str(n["number"])
        if not num_str.startswith("+"): num_str = "+" + num_str
        num_list += f"{icons[i]} <code>{num_str}</code>\n"
        
    text = (
        f"━━━━━━━━━━━\n"
        f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗨𝗠𝗕𝗘𝗥𝗦 𝗔𝗟𝗟𝗢𝗖𝗔𝗧𝗘𝗗 》\n"
        f"━━━━━━━━━━━\n"
        f"<b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> {service_name}\n"
        f"<b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {country}\n"
        f"━━━━━━━━━━━\n"
        f"{num_list}\n"
        f"━━━━━━━━━━━\n"
        f"<i>Wait for OTP in this bot or our group.</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Join OTP Group", url=get_settings()["otp_link"]))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
