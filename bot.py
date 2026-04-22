import telebot
import os
import json
import time
import requests
import re
import threading
import uuid
from telebot import types
from datetime import datetime

# --- CONFIGURATION ---
# Replace these with your actual credentials if not using environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8197284774"))
OTP_API_URL = os.environ.get("OTP_API_URL", "http://147.135.212.197/crapi/st/viewstats")
OTP_API_TOKEN = os.environ.get("OTP_API_TOKEN", "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- DATA STORAGE ---
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def read_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path): return []
    try:
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- ASSETS & EMOJIS ---
APP_EMOJIS = {
    'FACEBOOK': ('🚫', '5334807341109908955'), 'WHATSAPP': ('🚫', '5334759662677957452'),
    'TELEGRAM': ('🚫', '5337010556253543833'), 'WHATSAPPBUSINESSES': ('🚫', '5336814486701514414'),
    'IMO': ('🚫', '5337155807752524558'), 'INSTAGRAM': ('🚫', '5334868205091459431'),
    'APPLE': ('🚫', '5334637951894722661'), 'SNAPCHAT': ('🚫', '5334584041465222978'),
    'GOOGLE': ('🚫', '5335010201005231986'), 'BKASH': ('💸', '5348469219761626211'),
    'NAGAD': ('💴', '5352985330628730418'), 'YOUTUBE': ('🚫', '5334769042886533147')
}

PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DXA": "5334763399299506604",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "SUPPORT": "5337302974806922068",
    "ADMIN": "5353032893096567467", "USER": "5352861489541714456", "FILE": "5352721946054268944",
    "ROCKET": "5352597830089347330", "PIN": "5420517437885943844", "DOT": "5352638632278660622",
    "CLOSE": "5420130255174145507", "WAIT": "5336983442125001376", "CHAT": "5337302974806922068",
    "BROADCAST": "5352980533150259581", "UPLOAD": "5353001161878182134", "SETTINGS": "5420155432272438703"
}

# --- STATE MANAGEMENT ---
last_menus = {}
processed_messages = set()

def e(emoji, emoji_id):
    return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'

def get_settings():
    settings = read_json("settings.json")
    if not settings or isinstance(settings, list):
        settings = {
            "force_join": True,
            "channels": [{"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}],
            "admins": [], "otp_groups": [], "otp_link": "https://t.me/dxaotpzone",
            "brand_name": "DXA UNIVERSE", "mask_text": "DXA",
            "group_buttons": {}, "otp_message_buttons": []
        }
        write_json("settings.json", settings)
    return settings

def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    return str(user_id) in [str(a) for a in get_settings().get("admins", [])]

def check_join(user_id):
    settings = get_settings()
    if not settings.get("force_join", True) or is_admin(user_id): return True
    for channel in settings.get("channels", []):
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

# --- UI VIEWS ---
def show_force_join(chat_id, user_id):
    settings = get_settings()
    text = (f"{e('🚫', PREMIUM_EMOJIS['CLOSE'])} <b>ACCESS RESTRICTED</b> {e('🚫', PREMIUM_EMOJIS['CLOSE'])}\n"
            f"━━━━━━━━━━━━━\n"
            f"Please join our channel to use this bot.\n"
            f"━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    for c in settings.get("channels", []):
        markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
    markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="check_join_trigger"))
    sent = bot.send_message(chat_id, text, reply_markup=markup)
    last_menus[user_id] = sent.message_id

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📱 Get Number", "🛠 Support")
    if is_admin(user_id): markup.row("👑 Admin Panel")
    return markup

def show_services(chat_id, message_id=None, user_id=None):
    numbers = read_json("numbers.json")
    avail = [n for n in numbers if not n.get('used')]
    services = sorted(list(set([n['service'] for n in avail if n.get('service')])))
    markup = types.InlineKeyboardMarkup()
    if not services:
        text = f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} No numbers available."
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="close_menu"))
    else:
        text = f"{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>Select Service:</b>"
        for s in services: markup.add(types.InlineKeyboardButton(f"🔹 {s}", callback_data=f"sel_service:{s}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="close_menu"))
    
    if message_id: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        if user_id: last_menus[user_id] = sent.message_id

def show_admin_panel(chat_id, message_id=None, user_id=None):
    users = read_json("users.json")
    numbers = read_json("numbers.json")
    assigned = len([n for n in numbers if n.get('used')])
    total = len(numbers)
    avail = total - assigned
    bar_size = int((avail/total)*10) if total > 0 else 0
    bar = "█" * bar_size + "░" * (10 - bar_size)
    text = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN CONTROL PANEL</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"Users: {len(users)} | Stock: {avail}/{total}\n"
            f"Power: [{bar}]\n"
            f"━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload", callback_data="admin_upload"), types.InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), types.InlineKeyboardButton("🗑 Files", callback_data="admin_delete_files"))
    markup.row(types.InlineKeyboardButton("🚀 In-Stock", callback_data="view_unused"), types.InlineKeyboardButton("✅ Used", callback_data="view_used"))
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="close_menu"))
    if message_id: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        if user_id: last_menus[user_id] = sent.message_id

def show_settings_panel(chat_id, message_id):
    text = f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} <b>BOT SETTINGS CENTER</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📢 Force Join", callback_data="m_fj"), types.InlineKeyboardButton("👥 Admins", callback_data="m_adm"))
    markup.row(types.InlineKeyboardButton("💬 OTP Groups", callback_data="m_otp"), types.InlineKeyboardButton("✨ Brand/Mask", callback_data="m_brand"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

# --- HELPER LOGIC ---
def get_service_info(original_srv, content):
    text = content.upper()
    srv = original_srv
    keywords = [
        {'key': 'INSTAGRAM', 'name': 'Instagram'}, {'key': 'WHATSAPP', 'name': 'WhatsApp'},
        {'key': 'TELEGRAM', 'name': 'Telegram'}, {'key': 'FACEBOOK', 'name': 'Facebook'},
        {'key': 'GOOGLE', 'name': 'Google'}, {'key': 'TIKTOK', 'name': 'TikTok'},
        {'key': 'IMO', 'name': 'Imo'}, {'key': 'BKASH', 'name': 'bKash'}, {'key': 'NAGAD', 'name': 'Nagad'}
    ]
    for k in keywords:
        if k['key'] in text:
            srv = k['name']
            break
    s_key = srv.upper().replace(' ', '')
    prem = APP_EMOJIS.get(s_key)
    icon = e(prem[0], prem[1]) if prem else e("🖥", "5337302974806922068")
    return srv, icon

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = msg.from_user.id
    users = read_json("users.json")
    if not any(u['uid'] == str(u_id) for u in users):
        users.append({'uid': str(u_id), 'username': msg.from_user.username, 'time': str(datetime.now())})
        write_json("users.json", users)
    delete_last_menu(msg.chat.id, u_id)
    if not check_join(u_id): show_force_join(msg.chat.id, u_id); return
    text = (f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗡𝗨𝗠𝗕𝗘𝗥 𝗕𝗢𝗧 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 》═\n"
            f"━━━━━━━━━━━\n"
            f"{e('👋', PREMIUM_EMOJIS['HELLO'])} 𝗛𝗲𝗹𝗹𝗼, <b>{msg.from_user.first_name}</b>!\n"
            f"━━━━━━━━━━━")
    sent = bot.send_message(msg.chat.id, text, reply_markup=get_main_keyboard(u_id))
    last_menus[u_id] = sent.message_id

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    u_id, c_id, data = call.from_user.id, call.message.chat.id, call.data
    
    if data == "check_join_trigger":
        if check_join(u_id):
            bot.delete_message(c_id, call.message.message_id); start(call.message)
        else: bot.answer_callback_query(call.id, "❌ Not joined yet!", show_alert=True)
        return

    if not check_join(u_id):
        bot.answer_callback_query(call.id, "❌ Join channel first!", show_alert=True); return

    if data == "close_menu":
        bot.clear_step_handler_by_chat_id(c_id)
        try: bot.delete_message(c_id, call.message.message_id)
        except: pass
    elif data == "admin_panel_back":
        bot.clear_step_handler_by_chat_id(c_id); show_admin_panel(c_id, call.message.message_id)
    elif data == "admin_settings":
        show_settings_panel(c_id, call.message.message_id)
    elif data == "admin_broadcast":
        bot.edit_message_text("📢 <b>BROADCAST</b>\n━━━━━━━━━━━━━━\nSend ANY message (Media supported):", c_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back")))
        bot.register_next_step_handler(call.message, do_broadcast, call.message.message_id)
    elif data == "admin_upload":
        bot.edit_message_text("📤 <b>UPLOAD</b>\n━━━━━━━━━━━━━━\nSend a .txt file:", c_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back")))
        bot.register_next_step_handler(call.message, do_upload, call.message.message_id)
    elif data == "back_to_services":
        show_services(c_id, call.message.message_id)
    elif data.startswith("sel_service:"):
        srv = data.split(":")[1]
        nums = read_json("numbers.json")
        avail = [n for n in nums if not n.get('used') and n['service'] == srv]
        cnts = sorted(list(set([n['country'] for n in avail if n.get('country')])))
        markup = types.InlineKeyboardMarkup()
        for c in cnts: markup.add(types.InlineKeyboardButton(f"📍 {c}", callback_data=f"sel_cnt:{srv}:{c}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_services"))
        bot.edit_message_text(f"Select Country for <b>{srv}</b>:", c_id, call.message.message_id, reply_markup=markup)
    elif data.startswith("sel_cnt:"):
        parts = data.split(":")
        srv, country = parts[1], parts[2]
        all_nums = read_json("numbers.json")
        avail = [n for n in all_nums if not n.get('used') and n['service'] == srv and n['country'] == country]
        if not avail: bot.answer_callback_query(call.id, "Out of stock!", show_alert=True); return
        import random; sel = random.sample(avail, min(len(avail), 3))
        for s in sel: s['used'] = True; s['assignedTo'] = str(u_id); s['assignedAt'] = time.time()*1000
        write_json("numbers.json", all_nums)
        fmt = [f"<code>{n['number']}</code>" for n in sel]; name, icon = get_service_info(srv, "")
        text = (f"━━━━━━━━━━━\n"
                f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗨𝗠𝗕𝗘𝗥𝗦 𝗔𝗟𝗟𝗢𝗖𝗔𝗧𝗘𝗗 》\n"
                f"━━━━━━━━━━━\n"
                f"<blockquote>{e('🔹', PREMIUM_EMOJIS['DOT'])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲</b> {icon} <b>{srv}</b></blockquote>\n"
                f"<blockquote>{e('📍', PREMIUM_EMOJIS['PIN'])} <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆</b> 🌐 <b>{country}</b></blockquote>\n"
                f"━━━━━━━━━━━\n"
                f"{chr(10).join(fmt)}\n"
                f"━━━━━━━━━━━")
        markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("💬 OTP Group", url=get_settings().get("otp_link")))
        bot.edit_message_text(text, c_id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def h_msg(m):
    u_id = m.from_user.id
    if not check_join(u_id): show_force_join(m.chat.id, u_id); return
    if m.text == "📱 Get Number":
        delete_last_menu(m.chat.id, u_id); show_services(m.chat.id, user_id=u_id)
    elif m.text == "👑 Admin Panel" and is_admin(u_id):
        delete_last_menu(m.chat.id, u_id); show_admin_panel(m.chat.id, user_id=u_id)
    elif m.text == "🛠 Support":
        delete_last_menu(m.chat.id, u_id)
        sent = bot.send_message(m.chat.id, f"{e('🛠', PREMIUM_EMOJIS['SUPPORT'])} <b>Support:</b> @asik_x_bd_bot")
        last_menus[u_id] = sent.message_id

# --- ADMIN ACTIONS ---
def do_broadcast(msg, status_id):
    if msg.text and msg.text.startswith('/'): return
    users = read_json("users.json")
    status = bot.send_message(msg.chat.id, f"⏳ <b>Broadcasting...</b>\n0/{len(users)}", reply_to_message_id=status_id)
    ok = 0
    for i, u in enumerate(users):
        try: bot.copy_message(u['uid'], msg.chat.id, msg.message_id); ok += 1
        except: pass
        if (i+1)%10 == 0 or i == len(users)-1:
            try: bot.edit_message_text(f"⏳ <b>Broadcasting...</b>\nProgress: {i+1}/{len(users)}\nSuccess: {ok}", msg.chat.id, status.message_id); except: pass
    bot.edit_message_text(f"✅ <b>Broadcast Done!</b>\nSuccessful: {ok}\nFailed: {len(users)-ok}", msg.chat.id, status.message_id)

def do_upload(msg, status_id):
    if not msg.document or not msg.document.file_name.endswith('.txt'):
        bot.send_message(msg.chat.id, "❌ Send a .txt file."); return
    s = bot.send_message(msg.chat.id, "Service Name:"); bot.register_next_step_handler(s, lambda m: get_srv_for_up(m, msg.document))

def get_srv_for_up(m, doc):
    name = m.text; s = bot.send_message(m.chat.id, "Country Name:"); bot.register_next_step_handler(s, lambda m2: finish_up(m2, doc, name))

def finish_up(m, doc, srv):
    cnt = m.text; st = bot.send_message(m.chat.id, "⌛ Processing..."); 
    try:
        f = bot.get_file(doc.file_id); content = bot.download_file(f.file_path).decode('utf-8')
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        nums = read_json("numbers.json")
        for l in lines: nums.append({'id':str(uuid.uuid4())[:8], 'number':l, 'service':srv, 'country':cnt, 'used':False})
        write_json("numbers.json", nums); bot.edit_message_text(f"✅ {len(lines)} numbers added for {srv}!", m.chat.id, st.message_id)
    except Exception as x: bot.send_message(m.chat.id, f"❌ Error: {x}")

# --- OTP PROCESSOR ---
def fetch_otps():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50")
            if res.status_code == 200:
                data = res.json(); sets = get_settings(); nums = read_json("numbers.json")
                for rec in data:
                    if len(rec) < 4: continue
                    osrv, fnum, content, tstamp = rec
                    mid = f"{fnum}_{tstamp}"
                    if mid in processed_messages: continue
                    norm = re.sub(r'\D', '', fnum); otp_m = re.search(r'\d{4,8}', content)
                    code = otp_m.group(0) if otp_m else content
                    srv, icon = get_service_info(osrv, content)
                    markup = json.dumps({"inline_keyboard": [[{"text": f"📋 {code}", "copy_text": {"text": code}}]]})
                    for g_id in sets.get("otp_groups", []):
                        try: bot.send_message(g_id, f"{icon} {srv} <code>{norm}</code>\n\n{content}", reply_markup=markup); except: pass
                    match = next((n for n in nums if n.get('used') and re.sub(r'\D', '', str(n['number'])) == norm), None)
                    if match:
                        try: bot.send_message(match['assignedTo'], f"{icon} {srv} <code>{norm}</code>\n\n{content}", reply_markup=markup); except: pass
                    processed_messages.add(mid)
            time.sleep(5)
        except: time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=fetch_otps, daemon=True).start()
    bot.infinity_polling()
