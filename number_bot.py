import telebot
import os
import json
import time
import requests
import re
import threading
from telebot import types
from datetime import datetime

# --- Configuration ---
# You can set these in your .env or replace directly
BOT_TOKEN = "8332473503:AAEvyS-iBhm6eVp1VdEMYpTLhX5KEUu0WxQ"
ADMIN_ID = 8197284774
OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats"
OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ=="

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

FORCE_JOIN_CHANNELS = [
    {"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"},
    {"name": "Developer X Asik", "url": "https://t.me/developer_x_asik", "username": "@developer_x_asik"}
]

DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

APP_EMOJIS = {
    'FACEBOOK': ('🚫', '5334807341109908955'), 'WHATSAPP': ('🚫', '5334759662677957452'),
    'TELEGRAM': ('🚫', '5337010556253543833'), 'WHATSAPPBUSINESSES': ('🚫', '5336814486701514414'),
    'IMO': ('🚫', '5337155807752524558'), 'INSTAGRAM': ('🚫', '5334868205091459431'),
    'APPLE': ('🚫', '5334637951894722661'), 'FROZENICE': ('🚫', '5334530732331143967'),
    'NORDVPN': ('🚫', '5334944492300573096'), 'SNAPCHAT': ('🚫', '5334584041465222978'),
    'YOUTUBE': ('🚫', '5334769042886533147'), 'GOOGLE': ('🚫', '5335010201005231986'),
    'MICROSOFT': ('🖥', '5334880948259427772'), 'TEAMS': ('🌐', '5334590977837403844'),
    'MELBET': ('🌟', '5337102391244263212'), 'TIKTOK': ('🚫', '5339213256001102461'),
    'BKASH': ('💸', '5348469219761626211'), 'ROCKET_APP': ('💸', '5346042941196507141'),
    'BYBIT': ('💸', '5348372939479751825'), 'BINANCE': ('💸', '5348212415077064131'),
    'PROTONVPN': ('🥚', '5348390922507817684'), 'EXPRESSVPN': ('👨‍⚖️', '5346335574498251610'),
    'GMAIL': ('🐁', '5348494358205207761'), 'MESSENGER': ('🧻', '5348486915026884464'),
    'CHROME': ('⚗️', '5346311574221000149'), 'GOOGLEONE': ('🛴', '5348075478634766440'),
}

PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DXA": "5334763399299506604",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "SUPPORT": "5337302974806922068",
    "ADMIN": "5353032893096567467", "USER": "5352861489541714456", "FILE": "5352721946054268944",
    "NUMBERS": "5352862640592949843", "ROCKET": "5352597830089347330", "GRAPH": "5352877703043258544",
    "UPLOAD": "5353001161878182134", "BROADCAST": "5352980533150259581", "PIN": "5352922460897452503",
    "DOT": "5352638632278660622", "N1": "5352651766288652742", "N2": "5355186458418257716",
    "N3": "5352867219028091093", "WAIT": "5336983442125001376", "CLOSE": "5336997731481193790"
}

cooldowns = {}
processed_messages = set()
last_menus = {}

# --- Database Storage ---
def read_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def e(emoji, emoji_id):
    return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'

# --- Helpers ---
def check_join(user_id):
    for channel in FORCE_JOIN_CHANNELS:
        try:
            member = bot.get_chat_member(channel['username'], user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

def delete_last_menu(chat_id, user_id):
    if user_id in last_menus:
        try: bot.delete_message(chat_id, last_menus[user_id])
        except: pass
        del last_menus[user_id]

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📱 Get Number", "🛠 Support")
    if user_id == ADMIN_ID:
        markup.row("👑 Admin Panel")
    return markup

# --- Service Views ---
def show_services(chat_id, message_id=None, user_id=None):
    numbers = read_json("numbers.json")
    available = [n for n in numbers if not n.get('used', False)]
    services = sorted(list(set([n['service'] for n in available])))
    
    markup = types.InlineKeyboardMarkup()
    if not services:
        text = f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} No numbers available at the moment."
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="close_menu"))
    else:
        text = f"{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>Select a Service:</b>"
        for s in services:
            markup.add(types.InlineKeyboardButton(f"🔹 {s}", callback_data=f"sel_service:{s}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="close_menu"))

    if message_id:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except: pass
    else:
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        if user_id: last_menus[user_id] = sent.message_id

def show_admin_panel(chat_id, message_id=None, user_id=None):
    users = read_json("users.json")
    numbers = read_json("numbers.json")
    files = read_json("files.json")
    assigned = len([n for n in numbers if n.get('used')])
    available = len([n for n in numbers if not n.get('used')])
    total = len(numbers)
    
    percent = int((available / total) * 10) if total > 0 else 0
    bar = "█" * percent + "░" * (10 - percent)

    text = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN CONTROL PANEL</b> {e('👑', PREMIUM_EMOJIS['ADMIN'])}\n"
            f"━━━━━━━━━━━━━\n\n"
            f"{e('📊', PREMIUM_EMOJIS['GRAPH'])} <b>DATABASE OVERVIEW</b>\n"
            f"─ ─ ─ ─ ─ ─ ─\n"
            f"  {e('👤', PREMIUM_EMOJIS['USER'])}  Users       »  {len(users)}\n"
            f"  {e('📁', PREMIUM_EMOJIS['FILE'])}  Files       »  {len(files)}\n"
            f"  {e('🔢', PREMIUM_EMOJIS['NUMBERS'])}  Numbers     »  {total}\n"
            f"  {e('✅', PREMIUM_EMOJIS['DONE'])}  Assigned    »  {assigned}\n"
            f"  {e('🚀', PREMIUM_EMOJIS['ROCKET'])}  Available   »  {available}\n\n"
            f"{e('📈', PREMIUM_EMOJIS['GRAPH'])} <b>STOCK LEVEL</b>\n"
            f"─ ─ ─ ─ ─ ─ ─\n"
            f"  [{bar}]  {available} free\n\n"
            f"━━━━━━━━━━━━━")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload Numbers", callback_data="admin_upload"))
    markup.row(types.InlineKeyboardButton("🗑 Delete Files", callback_data="admin_delete_files"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
    markup.row(types.InlineKeyboardButton("✅ Used Numbers", callback_data="view_used"),
               types.InlineKeyboardButton("🚀 Unused Numbers", callback_data="view_unused"))
    markup.row(types.InlineKeyboardButton("🔙 Back", callback_data="close_menu"))

    if message_id:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except: pass
    else:
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        if user_id: last_menus[user_id] = sent.message_id

# --- Bot Handlers ---
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    users = read_json("users.json")
    if not any(u['uid'] == str(user_id) for u in users):
        users.append({'uid': str(user_id), 'username': msg.from_user.username, 'time': str(datetime.now())})
        write_json("users.json", users)

    if not check_join(user_id):
        markup = types.InlineKeyboardMarkup()
        for c in FORCE_JOIN_CHANNELS:
            markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="check_join"))
        bot.send_message(msg.chat.id, "You must join our channels to use this bot:", reply_markup=markup)
        return

    text = (f"{e('🔥', PREMIUM_EMOJIS['FIRE'])} DXA NUMBER BOT {e('🔥', PREMIUM_EMOJIS['FIRE'])}\n"
            f"━━━━━━━━━━━\n"
            f"{e('👋', PREMIUM_EMOJIS['HELLO'])} Hello, <b>{msg.from_user.first_name}</b>! Welcome To DXA UNIVERSE.\n\n"
            f"{e('📌', PREMIUM_EMOJIS['PIN'])} Tap Get Number to start!\n"
            f"━━━━━━━━━━━\n"
            f"{e('😒', PREMIUM_EMOJIS['DXA'])} POWERED BY DXA UNIVERSE")
    bot.send_message(msg.chat.id, text, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(func=lambda m: True)
def handle_msg(msg):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    
    if msg.text.startswith('/'): return
    if not check_join(user_id): return

    if msg.text == "📱 Get Number":
        try: bot.delete_message(chat_id, msg.message_id) 
        except: pass
        delete_last_menu(chat_id, user_id)
        show_services(chat_id, user_id=user_id)
        
    elif msg.text == "🛠 Support":
        try: bot.delete_message(chat_id, msg.message_id) 
        except: pass
        delete_last_menu(chat_id, user_id)
        text = (f"{e('🔥', PREMIUM_EMOJIS['FIRE'])} DXA SUPPORT CENTER {e('🔥', PREMIUM_EMOJIS['FIRE'])}\n"
                f"━━━━━━━━━━━\n"
                f"{e('👋', PREMIUM_EMOJIS['HELLO'])} Hello, <b>{msg.from_user.first_name}</b>! Tell Me How Can I Help You.\n\n"
                f"{e('📌', PREMIUM_EMOJIS['PIN'])} Tap Support Button to Contact The Admin!\n"
                f"━━━━━━━━━━━\n"
                f"{e('😒', PREMIUM_EMOJIS['DXA'])} POWERED BY DXA UNIVERSE")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Support Center", url="https://t.me/asik_x_bd_bot"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="close_menu"))
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        last_menus[user_id] = sent.message_id
        
    elif msg.text == "👑 Admin Panel" and user_id == ADMIN_ID:
        try: bot.delete_message(chat_id, msg.message_id) 
        except: pass
        delete_last_menu(chat_id, user_id)
        show_admin_panel(chat_id, user_id=user_id)

# --- Callback Handler ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data

    if data == "check_join":
        if check_join(user_id):
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)
            
    elif data == "close_menu":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        
    elif data.startswith("sel_service:"):
        service = data.split(":")[1]
        nums = read_json("numbers.json")
        available = [n for n in nums if not n.get('used') and n['service'] == service]
        countries = sorted(list(set([n['country'] for n in available])))
        
        markup = types.InlineKeyboardMarkup()
        for country in countries:
            markup.add(types.InlineKeyboardButton(f"📍 {country}", callback_data=f"sel_country:{service}:{country}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_services"))
        
        text = f"{e('📍', PREMIUM_EMOJIS['PIN'])} <b>Select Country for {service}:</b>"
        try: bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        except: pass
        
    elif data == "back_to_services":
        show_services(chat_id, call.message.message_id)
        
    elif data.startswith("sel_country:"):
        now = time.time() * 1000
        last_time = cooldowns.get(user_id, 0)
        diff = (now - last_time) / 1000
        
        if diff < 10:
            bot.answer_callback_query(call.id, f"❌ Please wait {int(10-diff)} seconds!", show_alert=True)
            return

        parts = data.split(":")
        service, country = parts[1], parts[2]
        all_nums = read_json("numbers.json")
        available = [n for n in all_nums if not n.get('used') and n.get('service') == service and n.get('country') == country]
        
        if len(available) < 3:
            bot.answer_callback_query(call.id, "❌ Not enough numbers available.", show_alert=True)
            return
            
        import random
        selected = random.sample(available, 3)
        selected_ids = [s['id'] for s in selected]
        
        for n in all_nums:
            if n['id'] in selected_ids:
                n['used'] = True
                n['assignedTo'] = str(user_id)
                n['assignedAt'] = now
        write_json("numbers.json", all_nums)
        cooldowns[user_id] = now
        
        icons = [e("1️⃣", PREMIUM_EMOJIS['N1']), e("2️⃣", PREMIUM_EMOJIS['N2']), e("3️⃣", PREMIUM_EMOJIS['N3'])]
        formatted = []
        for i, n in enumerate(selected):
            num = str(n['number']).strip()
            if not num.startswith("+"): num = "+" + num
            formatted.append(f"{icons[i]} <code>{num}</code>")

        text = (f"{e('✅', PREMIUM_EMOJIS['DONE'])} <b>NUMBERS ALLOCATED</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f" {e('🔹', PREMIUM_EMOJIS['DOT'])} Service: <b>{service}</b>\n"
                f" {e('📍', PREMIUM_EMOJIS['PIN'])} Country: <b>{country}</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"{chr(10).join(formatted)}\n"
                f"━━━━━━━━━━━━━━\n"
                f"{e('😒', PREMIUM_EMOJIS['DXA'])} POWERED BY DXA UNIVERSE")
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"sel_country:{service}:{country}"))
        markup.row(types.InlineKeyboardButton("💬 OTP Group", url="https://t.me/dxaotpzone"))
        markup.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_services"))
        
        try: bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        except: pass

    elif data == "admin_upload":
        text = f"{e('📤', PREMIUM_EMOJIS['UPLOAD'])} <b>UPLOAD NUMBERS</b>\n━━━━━━━━━━━━━\nPlease send the .txt file containing numbers."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        
        @bot.message_handler(content_types=['document'])
        def handle_upload(dmsg):
            if dmsg.from_user.id != ADMIN_ID: return
            if not dmsg.document.file_name.endswith('.txt'):
                bot.send_message(chat_id, "❌ Please send a valid .txt file.")
                return
            
            s_msg = bot.send_message(chat_id, f"{e('🔹', PREMIUM_EMOJIS['DOT'])} Enter Service Name:", parse_mode='HTML')
            bot.register_next_step_handler(s_msg, lambda m: process_service_name(m, dmsg.document))

        def process_service_name(m, doc):
            service_name = m.text
            c_msg = bot.send_message(chat_id, f"{e('📍', PREMIUM_EMOJIS['PIN'])} Enter Country Name:", parse_mode='HTML')
            bot.register_next_step_handler(c_msg, lambda m2: process_country_name(m2, doc, service_name))

        def process_country_name(m, doc, service_name):
            country_name = m.text
            wait_msg = bot.send_message(chat_id, f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} Processing...", parse_mode='HTML')
            
            try:
                file_info = bot.get_file(doc.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                content = downloaded_file.decode('utf-8')
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                
                numbers = read_json("numbers.json")
                files = read_json("files.json")
                fid = str(int(time.time()))
                
                files.append({'id': fid, 'fileName': doc.file_name, 'service': service_name, 'country': country_name, 'count': len(lines)})
                import uuid
                for line in lines:
                    numbers.append({
                        'id': str(uuid.uuid4())[:8],
                        'number': line,
                        'service': service_name,
                        'country': country_name,
                        'used': False,
                        'fileId': fid
                    })
                
                write_json("numbers.json", numbers)
                write_json("files.json", files)
                bot.delete_message(chat_id, wait_msg.message_id)
                bot.send_message(chat_id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Success! {len(lines)} numbers added.")
            except Exception as ex:
                bot.send_message(chat_id, f"❌ Error: {str(ex)}")

    elif data == "admin_broadcast":
        text = f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} <b>BROADCAST MESSAGE</b>\n━━━━━━━━━━━━━\nSend message to broadcast:"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
        msg = bot.send_message(chat_id, text, reply_markup=markup)
        bot.register_next_step_handler(msg, process_broadcast)

    elif data == "admin_delete_files":
        files = read_json("files.json")
        if not files:
            bot.answer_callback_query(call.id, "No files found.")
            return
        markup = types.InlineKeyboardMarkup()
        for f in files:
            markup.add(types.InlineKeyboardButton(f"❌ {f['fileName']} ({f['service']})", callback_data=f"del_file:{f['id']}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
        bot.edit_message_text("Select a file to delete:", chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("del_file:"):
        fid = data.split(":")[1]
        files = read_json("files.json")
        nums = read_json("numbers.json")
        files = [f for f in files if f['id'] != fid]
        nums = [n for n in nums if n.get('fileId') != fid]
        write_json("files.json", files)
        write_json("numbers.json", nums)
        bot.answer_callback_query(call.id, "✅ Deleted!")
        show_admin_panel(chat_id, call.message.message_id)

    elif data == "view_used" or data == "view_unused":
        is_used = "used" in data
        nums = [n for n in read_json("numbers.json") if n.get('used') == is_used]
        text = f"<b>{data.replace('view_', '').upper()} NUMBERS</b>\nTotal: {len(nums)}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Download (.txt)", callback_data=f"download_{'used' if is_used else 'unused'}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("download_"):
        is_used = "used" in data
        nums = [n['number'] for n in read_json("numbers.json") if n.get('used') == is_used]
        if not nums:
            bot.answer_callback_query(call.id, "Empty list.")
            return
        import io
        buf = io.BytesIO("\n".join(nums).encode())
        buf.name = f"{'used' if is_used else 'unused'}.txt"
        bot.send_document(chat_id, buf)

    elif data == "admin_panel_back":
        show_admin_panel(chat_id, call.message.message_id)

def process_broadcast(msg):
    users = read_json("users.json")
    count = 0
    for u in users:
        try:
            bot.copy_message(u['uid'], msg.chat.id, msg.message_id)
            count += 1
        except: pass
    bot.send_message(msg.chat.id, f"✅ Broadcast complete! Sent to {count} users.")

# --- OTP Background Processor ---
def normalize_num(num):
    return re.sub(r'\D', '', str(num))

def fetch_otps():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50")
            if res.status_code == 200:
                data = res.json()
                nums_data = read_json("numbers.json")
                for rec in data:
                    if len(rec) < 4: continue
                    serv, full_num, content, tstamp = rec
                    msg_id = f"{full_num}_{tstamp}"
                    if msg_id in processed_messages: continue
                    
                    norm_api = normalize_num(full_num)
                    match = next((n for n in nums_data if n.get('used') and (normalize_num(n['number']) == norm_api or normalize_num(n['number']).endswith(norm_api) or norm_api.endswith(normalize_num(n['number'])))), None)
                    
                    if match:
                        iso_ts = tstamp.replace(" ", "T") if " " in tstamp else tstamp
                        try:
                            msg_time = datetime.fromisoformat(iso_ts).timestamp() * 1000
                            # Reject if older than 24h
                            if msg_time < (match.get('assignedAt', 0) - 86400000):
                                processed_messages.add(msg_id)
                                continue
                        except: pass

                        # Extract OTP
                        otp_match = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                        if otp_match:
                            code = otp_match.group(0)
                            serv_key = str(serv).upper().replace(" ", "")
                            premium = APP_EMOJIS.get(serv_key)
                            icon = e(premium[0], premium[1]) if premium else e("💬", "5337302974806922068")
                            
                            # Format: Icon Service Number
                            body = f"{icon} <b>{serv}</b>  <code>{norm_api}</code>"
                            # Attempt to use native copy_text structure if possible in raw dict
                            # For pyTelegramBotAPI, we can use a dict for the markup to include newer fields
                            markup = {
                                "inline_keyboard": [
                                    [{
                                        "text": f"📋 {code}",
                                        "copy_text": {"text": code}
                                    }]
                                ]
                            }
                            bot.send_message(match['assignedTo'], body, reply_markup=json.dumps(markup))
                            processed_messages.add(msg_id)
            time.sleep(5)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=fetch_otps, daemon=True).start()
    print("Bot is running...")
    bot.infinity_polling()
