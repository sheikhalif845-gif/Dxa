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

# --- CONFIGURATION (Mirroring App Perfectly) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8197284774"))
OTP_API_URL = os.environ.get("OTP_API_URL", "http://147.135.212.197/crapi/st/viewstats")
OTP_API_TOKEN = os.environ.get("OTP_API_TOKEN", "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- DATA STORAGE ENGINE ---
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

def get_settings():
    s = read_json("settings.json")
    if not s or isinstance(s, list):
        s = {
            "force_join": True,
            "channels": [{"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}],
            "admins": [], "otp_groups": [], "otp_link": "https://t.me/dxaotpzone",
            "brand_name": "DXA UNIVERSE", "mask_text": "DXA",
            "group_buttons": {}, "otp_message_buttons": []
        }
        write_json("settings.json", s)
    return s

def is_admin(uid):
    if str(uid) == str(ADMIN_ID): return True
    return str(uid) in [str(a) for a in get_settings().get("admins", [])]

# --- ASSETS & EMOJIS (100% Mirror) ---
APP_EMOJIS = {
    'FACEBOOK': ('🚫', '5334807341109908955'), 'WHATSAPP': ('🚫', '5334759662677957452'),
    'TELEGRAM': ('🚫', '5337010556253543833'), 'IMO': ('🚫', '5337155807752524558'),
    'INSTAGRAM': ('🚫', '5334868205091459431'), 'GOOGLE': ('🚫', '5335010201005231986'),
    'BKASH': ('💸', '5348469219761626211'), 'NAGAD': ('💴', '5352985330628730418'),
    'TIKTOK': ('🚫', '5339213256001102461'), 'BINANCE': ('💰', '5348212415077064131')
}

PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DXA": "5334763399299506604",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "SUPPORT": "5337302974806922068",
    "ADMIN": "5353032893096567467", "USER": "5352861489541714456", "FILE": "5352721946054268944",
    "ROCKET": "5352597830089347330", "PIN": "5420517437885943844", "DOT": "5352638632278660622",
    "CLOSE": "5420130255174145507", "WAIT": "5336983442125001376", "BROADCAST": "5352980533150259581", 
    "UPLOAD": "5353001161878182134", "SETTINGS": "5420155432272438703"
}

# --- STATE ---
processed_messages = set()
last_number_otp = {}
last_menus = {}

def e(emoji, emoji_id):
    return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'

def check_join(uid):
    s = get_settings()
    if not s.get("force_join", True) or is_admin(uid): return True
    for c in s.get("channels", []):
        try:
            m = bot.get_chat_member(c['username'], uid)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

# --- UI VIEWS ---
def get_main_keyboard(u_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📱 Get Number", "🛠 Support")
    if is_admin(u_id): markup.row("👑 Admin Panel")
    return markup

def show_admin_panel(c_id, m_id=None, u_id=None):
    users = read_json("users.json"); numbers = read_json("numbers.json")
    assigned = len([n for n in numbers if n.get('used')])
    total = len(numbers); avail = total - assigned
    bar_size = int((avail/total)*10) if total > 0 else 0
    bar = "█" * bar_size + "░" * (10 - bar_size)
    text = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN CONTROL PANEL</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"Users: {len(users)} | Stock: {avail}/{total}\n"
            f"Power: [{bar}]\n"
            f"━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload", callback_data="adm_upload"), types.InlineKeyboardButton("⚙️ Settings", callback_data="adm_settings"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"), types.InlineKeyboardButton("🗑 Files", callback_data="adm_files"))
    markup.row(types.InlineKeyboardButton("🚀 In-Stock", callback_data="v_avail"), types.InlineKeyboardButton("✅ Used", callback_data="v_used"))
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="close_menu"))
    if m_id: bot.edit_message_text(text, c_id, m_id, reply_markup=markup)
    else: 
        sent = bot.send_message(c_id, text, reply_markup=markup)
        if u_id: last_menus[u_id] = sent.message_id

def show_settings(c_id, m_id):
    s = get_settings(); fj = "✅ ON" if s['force_join'] else "❌ OFF"
    text = (f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} <b>SETTINGS CENTER</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"Force Join: <b>{fj}</b>\n"
            f"Brand: <b>{s['brand_name']}</b>")
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton(f"Force Join: {fj}", callback_data="toggle_fj"))
    mk.row(types.InlineKeyboardButton("📢 Channels", callback_data="m_chan"), types.InlineKeyboardButton("👥 Admins", callback_data="m_adm"))
    mk.row(types.InlineKeyboardButton("💬 Groups", callback_data="m_grp"), types.InlineKeyboardButton("✨ Branding", callback_data="m_brand"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
    bot.edit_message_text(text, c_id, m_id, reply_markup=mk)

# --- OTP PROCESSOR (Content-based Deduplication) ---
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
                    mid, norm = f"{fnum}_{tstamp}", re.sub(r'\D', '', fnum)
                    if mid in processed_messages: continue
                    
                    # Deduplication Logic
                    otp_m = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                    code = otp_m.group(0) if otp_m else content
                    if last_number_otp.get(norm) == code:
                        processed_messages.add(mid); continue
                    
                    last_number_otp[norm] = code; processed_messages.add(mid)
                    icon_data = APP_EMOJIS.get(osrv.upper().replace(' ', ''))
                    icon = e(icon_data[0], icon_data[1]) if icon_data else e("🖥", "5337302974806922068")
                    
                    mask = sets.get("mask_text", "DXA")
                    maskedNum = norm if len(norm) < 7 else f"{norm[:3]}{mask}{norm[-4:]}"
                    
                    #Design: Replicating User's requested formatting
                    text = (f"━━━━━━━━━━━\n"
                            f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} <b>𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘</b> 》\n"
                            f"━━━━━━━━━━━\n"
                            f"<blockquote>{e('🔹', PREMIUM_EMOJIS['DOT'])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>{osrv}</b></blockquote>\n"
                            f"<blockquote>{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>{maskedNum}</code></blockquote>\n"
                            f"━━━━━━━━━━━\n"
                            f"<blockquote>{e('💬', PREMIUM_EMOJIS['FIRE'])} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>{content}</code></blockquote>\n"
                            f"━━━━━━━━━━━\n"
                            f"<i>{sets['brand_name']}</i>")
                    
                    markup = json.dumps({"inline_keyboard": [[{"text": f"📋 {code}", "copy_text": {"text": code}}]]})
                    for g_id in sets.get("otp_groups", []):
                        try: bot.send_message(g_id, text, reply_markup=markup); except: pass
                    match = next((n for n in nums if n.get('used') and re.sub(r'\D', '', str(n['number'])) == norm), None)
                    if match:
                        try: bot.send_message(match['assignedTo'], text, reply_markup=markup); except: pass
            time.sleep(5)
        except: time.sleep(10)

# --- BROADCAST HANDLER ---
def start_bc(msg, sid):
    if msg.text and msg.text.startswith('/'): return
    users = read_json("users.json"); status = bot.send_message(msg.chat.id, f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} <b>Broadcasting...</b>\n0/{len(users)}")
    ok = 0
    for i, u in enumerate(users):
        try: bot.copy_message(u['uid'], msg.chat.id, msg.message_id); ok += 1
        except: pass
        if (i+1)%10 == 0 or i == len(users)-1:
            try: bot.edit_message_text(f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} <b>Broadcasting...</b>\nProgress: {i+1}/{len(users)}\nSuccess: {ok}", msg.chat.id, status.message_id); except: pass
    bot.edit_message_text(f"{e('✅', PREMIUM_EMOJIS['DONE'])} <b>Done!</b> Sent to {ok} users.", msg.chat.id, status.message_id)

# --- BOT ROUTERS ---
@bot.message_handler(commands=['start'])
def start_h(msg):
    u_id = msg.from_user.id; users = read_json("users.json")
    if not any(u['uid'] == str(u_id) for u in users):
        users.append({'uid': str(u_id), 'username': msg.from_user.username, 'time': str(datetime.now())})
        write_json("users.json", users)
    if not check_join(u_id):
        s = get_settings(); mk = types.InlineKeyboardMarkup()
        for c in s['channels']: mk.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
        mk.add(types.InlineKeyboardButton("Joined ✅", callback_data="check_j"))
        bot.send_message(msg.chat.id, f"{e('🚫', PREMIUM_EMOJIS['CLOSE'])} <b>Access Restricted!</b>\nJoin first.", reply_markup=mk)
        return
    bot.send_message(msg.chat.id, f"Hello!", reply_markup=get_main_keyboard(u_id))

@bot.callback_query_handler(func=lambda call: True)
def calls(call):
    u_id, c_id, d = call.from_user.id, call.message.chat.id, call.data
    if d == "admin_panel_back": show_admin_panel(c_id, call.message.message_id)
    elif d == "adm_settings": show_settings(c_id, call.message.message_id)
    elif d == "toggle_fj":
        s = get_settings(); s['force_join'] = not s['force_join']; write_json("settings.json", s); show_settings(c_id, call.message.message_id)
    elif d == "adm_broadcast":
        bot.edit_message_text("📢 Send ANY Message (Support Media):", c_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back")))
        bot.register_next_step_handler(call.message, start_bc, call.message.message_id)
    elif d == "check_j":
        if check_join(u_id): bot.delete_message(c_id, call.message.message_id); start_h(call.message)
        else: bot.answer_callback_query(call.id, "❌ Not joined!", show_alert=True)
    elif d == "close_menu": bot.delete_message(c_id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def text_router(m):
    u_id = m.from_user.id
    if not check_join(u_id): return
    if m.text == "👑 Admin Panel" and is_admin(u_id): show_admin_panel(m.chat.id, u_id=u_id)
    elif m.text == "📱 Get Number":
        nums = read_json("numbers.json"); avail = [n for n in nums if not n.get('used')]
        srvs = sorted(list(set([n['service'] for n in avail if n.get('service')])))
        mk = types.InlineKeyboardMarkup()
        for s in srvs: mk.add(types.InlineKeyboardButton(f"🔹 {s}", callback_data=f"sel_srv:{s}"))
        bot.send_message(m.chat.id, f"{e('📱', PREMIUM_EMOJIS['NUMBER'])} Select Service:", reply_markup=mk)

if __name__ == "__main__":
    threading.Thread(target=fetch_otps, daemon=True).start()
    bot.infinity_polling()
