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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8197284774"))
OTP_API_URL = os.environ.get("OTP_API_URL", "http://147.135.212.197/crapi/st/viewstats")
OTP_API_TOKEN = os.environ.get("OTP_API_TOKEN", "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- DATA STORAGE ---
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

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

# --- STATE ---
last_menus = {}
processed_messages = set()
last_number_otp = {} # Track last OTP per number

def e(emoji, emoji_id):
    return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'

def get_settings():
    settings = read_json("settings.json")
    if not settings or isinstance(settings, list):
        settings = {
            "force_join": True,
            "channels": [{"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}],
            "admins": [], "otp_groups": [], "otp_link": "https://t.me/dxaotpzone",
            "brand_name": "DXA UNIVERSE", "mask_text": "DXA"
        }
        write_json("settings.json", settings)
    return settings

def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    return str(user_id) in [str(a) for a in get_settings().get("admins", [])]

def check_join(user_id):
    settings = get_settings()
    if not settings.get("force_join", True) or is_admin(user_id): return True
    for c in settings.get("channels", []):
        try:
            m = bot.get_chat_member(c['username'], user_id)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

def delete_last_menu(c_id, u_id):
    if u_id in last_menus:
        try: bot.delete_message(c_id, last_menus[u_id]); except: pass
        del last_menus[u_id]

# --- UI VIEWS (Sync with App Design) ---
def show_admin_panel(c_id, m_id=None, u_id=None):
    users = read_json("users.json"); numbers = read_json("numbers.json")
    assigned = len([n for n in numbers if n.get('used')])
    total = len(numbers); avail = total - assigned
    bar = "█" * int((avail/total)*10) if total > 0 else ""
    text = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN PANEL</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"Users: {len(users)} | Stock: {avail}/{total}\n"
            f"Power: [{bar.ljust(10, '░')}]\n"
            f"━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload", callback_data="admin_upload"), types.InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), types.InlineKeyboardButton("🗑 Files", callback_data="admin_delete_files"))
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="close_menu"))
    if m_id: bot.edit_message_text(text, c_id, m_id, reply_markup=markup)
    else:
        sent = bot.send_message(c_id, text, reply_markup=markup)
        if u_id: last_menus[u_id] = sent.message_id

def show_settings(c_id, m_id):
    text = f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} <b>SETTINGS CENTER</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📢 Force Join", callback_data="m_fj"), types.InlineKeyboardButton("👥 Admins", callback_data="m_adm"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
    bot.edit_message_text(text, c_id, m_id, reply_markup=markup)

def get_main_keyboard(u_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📱 Get Number", "🛠 Support")
    if is_admin(u_id): markup.row("👑 Admin Panel")
    return markup

# --- CORE HANDLERS ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = msg.from_user.id
    users = read_json("users.json")
    if not any(u['uid'] == str(u_id) for u in users):
        users.append({'uid': str(u_id), 'username': msg.from_user.username, 'time': str(datetime.now())})
        write_json("users.json", users)
    delete_last_menu(msg.chat.id, u_id)
    if not check_join(u_id):
        show_force_join(msg.chat.id, u_id); return
    text = (f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗡𝗨ＭＢ𝗘𝗥 𝗕𝗢𝗧 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 》═\n"
            f"━━━━━━━━━━━\n"
            f"{e('👋', PREMIUM_EMOJIS['HELLO'])} 𝗛𝗲𝗹𝗹𝗼, <b>{msg.from_user.first_name}</b>!\n"
            f"━━━━━━━━━━━")
    sent = bot.send_message(msg.chat.id, text, reply_markup=get_main_keyboard(u_id))
    last_menus[u_id] = sent.message_id

@bot.callback_query_handler(func=lambda call: True)
def query_router(call):
    u_id, c_id, data = call.from_user.id, call.message.chat.id, call.data
    if data == "check_join_trigger":
        if check_join(u_id): bot.delete_message(c_id, call.message.message_id); start(call.message)
        else: bot.answer_callback_query(call.id, "❌ Not joined!", show_alert=True)
        return
    if not check_join(u_id): bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True); return

    if data == "close_menu":
        bot.clear_step_handler_by_chat_id(c_id)
        try: bot.delete_message(c_id, call.message.message_id); except: pass
    elif data == "admin_panel_back":
        bot.clear_step_handler_by_chat_id(c_id); show_admin_panel(c_id, call.message.message_id)
    elif data == "admin_settings":
        show_settings(c_id, call.message.message_id)
    elif data == "admin_broadcast":
        bot.edit_message_text("📢 <b>BROADCAST</b>\n━━━━━━━━━━━━━\nSend ANY message (Media/Text):", c_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back")))
        bot.register_next_step_handler(call.message, do_bc, call.message.message_id)
    # Further admin handlers for channels, admins, group management should go here for full replication.
    # ... simplified for mirror demo ...

@bot.message_handler(func=lambda m: True)
def msg_router(m):
    u_id = m.from_user.id
    if not check_join(u_id): show_force_join(m.chat.id, u_id); return
    if m.text == "📱 Get Number":
        nums = read_json("numbers.json"); avail = [n for n in nums if not n.get('used')]
        srvs = sorted(list(set([n['service'] for n in avail if n.get('service')])))
        markup = types.InlineKeyboardMarkup()
        for s in srvs: markup.add(types.InlineKeyboardButton(f"🔹 {s}", callback_data=f"sel_srv:{s}"))
        sent = bot.send_message(m.chat.id, "Select Service:", reply_markup=markup)
        last_menus[u_id] = sent.message_id
    elif m.text == "👑 Admin Panel" and is_admin(u_id):
        show_admin_panel(m.chat.id, u_id=u_id)

def do_bc(msg, status_id):
    if msg.text and msg.text.startswith('/'): return
    users = read_json("users.json")
    status = bot.send_message(msg.chat.id, f"⏳ <b>Broadcasting...</b>\n0/{len(users)}")
    ok = 0
    for i, u in enumerate(users):
        try: bot.copy_message(u['uid'], msg.chat.id, msg.message_id); ok += 1
        except: pass
        if (i+1)%10 == 0 or i == len(users)-1:
            try: bot.edit_message_text(f"⏳ <b>Broadcasting...</b>\nProgress: {i+1}/{len(users)}\nSuccess: {ok}", msg.chat.id, status.message_id); except: pass
    bot.edit_message_text(f"✅ <b>Done!</b>\nSent: {ok}\nFailed: {len(users)-ok}", msg.chat.id, status.message_id)

# --- OTP FETCH ENGINE (Mirroring App Logic) ---
def fetch_otps():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50")
            if res.status_code == 200:
                try: data = res.json()
                except: time.sleep(10); continue
                sets = get_settings(); nums = read_json("numbers.json")
                for rec in data:
                    if len(rec) < 4: continue
                    osrv, fnum, content, tstamp = rec
                    mid = f"{fnum}_{tstamp}"
                    norm = re.sub(r'\D', '', fnum)
                    
                    if mid in processed_messages: continue
                    
                    # Deduplication check: Same code for same number
                    otp_m = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                    code = otp_m.group(0) if otp_m else content
                    
                    if last_number_otp.get(norm) == code:
                        processed_messages.add(mid); continue
                    
                    last_number_otp[norm] = code
                    processed_messages.add(mid)
                    
                    # Design: Quotes for Service & Country
                    text = (f"━━━━━━━━━━━\n"
                            f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} <b>𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘</b> 》\n"
                            f"━━━━━━━━━━━\n"
                            f"<blockquote>𝗦𝗲𝗿𝘃𝗶𝗰𝗲: <b>{osrv}</b></blockquote>\n"
                            f"<blockquote>𝗡𝘂𝗺𝗯𝗲𝗿: <code>{norm}</code></blockquote>\n"
                            f"━━━━━━━━━━━\n"
                            f"<blockquote>𝗖𝗼𝗻𝘁𝗲𝗻𝘁: <code>{content}</code></blockquote>\n"
                            f"━━━━━━━━━━━")
                    markup = json.dumps({"inline_keyboard": [[{"text": f"📋 {code}", "copy_text": {"text": code}}]]})
                    
                    for g_id in sets.get("otp_groups", []):
                        try: bot.send_message(g_id, text, reply_markup=markup); except: pass
                    match = next((n for n in nums if n.get('used') and re.sub(r'\D', '', str(n['number'])) == norm), None)
                    if match:
                        try: bot.send_message(match['assignedTo'], text, reply_markup=markup); except: pass
            time.sleep(5)
        except: time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=fetch_otps, daemon=True).start()
    bot.infinity_polling()
