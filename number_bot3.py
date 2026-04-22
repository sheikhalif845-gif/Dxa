# --- Part 4: OTP Monitoring logic ---
processed_otps = set()
last_codes_map = {}

def start_otp_monitor():
    """Background task to fetch and forward OTPs"""
    while True:
        try:
            settings = get_settings()
            response = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50", timeout=10)
            if response.status_code == 200:
                data = response.json()
                numbers_db = read_json("numbers.json")
                
                for entry in data:
                    service, raw_num, content, timestamp = entry
                    entry_id = f"{raw_num}_{timestamp}"
                    
                    if entry_id in processed_otps: continue
                    
                    # 1. Extract Logic
                    code_match = re.findall(r'\d{4,8}', content)
                    code = code_match[0] if code_match else content
                    normalized_num = "".join(filter(str.isdigit, raw_num))
                    
                    # 2. Debounce matching codes
                    if last_codes_map.get(normalized_num) == code:
                        processed_otps.add(entry_id)
                        continue
                        
                    last_codes_map[normalized_num] = code
                    processed_otps.add(entry_id)
                    
                    # 3. Branding & Masking
                    brand = settings.get("brand_name", "DXA UNIVERSE")
                    mask = settings.get("mask_text", "DXA")
                    masked_num = f"{normalized_num[:3]}{mask}{normalized_num[-4:]}" if len(normalized_num) > 7 else normalized_num
                    
                    icon = get_app_icon(service)
                    
                    message_text = (
                        f"━━━━━━━━━━━\n"
                        f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 》\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{icon} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>{service}</b></blockquote>\n"
                        f"<blockquote>{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>{masked_num}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>{content}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<i>{brand}</i>"
                    )
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(f"📋 {code}", callback_data="none"))
                    for btn in settings.get("otp_message_buttons", []):
                        markup.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
                    
                    # 4. Forward to Groups
                    for group_id in settings.get("otp_groups", []):
                        try: bot.send_message(group_id, message_text, reply_markup=markup)
                        except: pass
                        
                    # 5. Direct Message to Assigned User
                    # Check numbers.json for matches
                    for num in numbers_db:
                        if num.get("used") and "".join(filter(str.isdigit, str(num["number"]))).endswith(normalized_num[-8:]):
                            try: bot.send_message(num["assignedTo"], message_text, reply_markup=markup)
                            except: pass
                            break
        except Exception as e: print(f"Monitor error: {e}")
        time.sleep(5)
