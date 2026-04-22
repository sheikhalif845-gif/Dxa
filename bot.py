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

# ==========================================
# ⚙️ CONFIGURATION (SYNC WITH DASHBOARD)
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8197284774"))
OTP_API_URL = os.environ.get("OTP_API_URL", "http://147.135.212.197/crapi/st/viewstats")
OTP_API_TOKEN = os.environ.get("OTP_API_TOKEN", "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- DATA STORAGE ---
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# ==========================================
# 📊 DATABASE ENGINE (MIRRORING APP)
# ==========================================
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

# ==========================================
# 🎨 ASSET CONSTANTS (SYNC WITH PREMIUM)
# ==========================================
PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DONE": "5352694861990501856",
    "NUMBER": "5337132498965010628", "ADMIN": "5353032893096567467", "CLOSE": "5420130255174145507",
    "SETTINGS": "5420155432272438703", "DOT": "5352638632278660622", "PIN": "5420517437885943844",
    "UPLOAD": "5353001161878182134", "BROADCAST": "5352980533150259581", "WAIT": "5336983442125001376",
    "ROCKET": "5352597830089347330", "USER": "5352861489541714456", "FILE": "5352721946054268944"
}

APP_EMOJIS = {
    'FACEBOOK': ('🚫', '5334807341109908955'), 'WHATSAPP': ('🚫', '5334759662677957452'),
    'TELEGRAM': ('🚫', '5337010556253543833'), 'IMO': ('🚫', '5337155807752524558'), 
    'INSTAGRAM': ('🚫', '5334868205091459431'), 'GOOGLE': ('🚫', '5335010201005231986'),
    'BKASH': ('💸', '5348469219761626211'), 'NAGAD': ('💴', '5352985330628730418'),
    'TIKTOK': ('🚫', '5339213256001102461')
}

def e(emoji, eid):
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# --- STATE TRACKERS ---
last_menus = {}
processed_messages = set()
last_number_otp = {} 

# ==========================================
# 🏗️ CORE MIDDLEWARE (JOIN & ADMIN)
# ==========================================
def is_admin(uid):
    if str(uid) == str(ADMIN_ID): return True
    return str(uid) in [str(a) for a in get_settings().get("admins", [])]

def check_join(uid):
    s = get_settings()
    if not s.get("force_join", True) or is_admin(uid): return True
    for c in s.get("channels", []):
        try:
            m = bot.get_chat_member(c['username'], uid)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

def delete_last_menu(c_id, u_id):
    if u_id in last_menus:
        try: bot.delete_message(c_id, last_menus[u_id]); except: pass
        del last_menus[u_id]

# ==========================================
# 🏛️ UI INTERFACE (MIRRORING DASHBOARD)
# ==========================================
def get_main_keyboard(u_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 Get Number", "🛠 Support")
    if is_admin(u_id): kb.row("👑 Admin Panel")
    return kb

def show_admin_panel(c_id, m_id=None, u_id=None):
    users = read_json("users.json"); nums = read_json("numbers.json")
    assigned = len([n for n in nums if n.get('used')]); avail = len(nums) - assigned
    bar = "█" * int((avail/len(nums))*10) if len(nums) > 0 else ""
    text = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN CONTROL PANEL</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"{e('👥', PREMIUM_EMOJIS['USER'])} Users: <b>{len(users)}</b>\n"
            f"{e('🚀', PREMIUM_EMOJIS['ROCKET'])} Stock: <b>{avail}/{len(nums)}</b>\n"
            f"Power: [{bar.ljust(10, '░')}]\n"
            f"━━━━━━━━━━━━━")
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton("📤 Upload", callback_data="adm_up"), types.InlineKeyboardButton("⚙️ Settings", callback_data="adm_sets"))
    mk.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"), types.InlineKeyboardButton("🗑 Files", callback_data="adm_files"))
    mk.add(types.InlineKeyboardButton("🚀 In-Stock", callback_data="v_avail"), types.InlineKeyboardButton("✅ Used List", callback_data="v_used"))
    mk.add(types.InlineKeyboardButton("🔙 Close", callback_data="close"))
    if m_id: bot.edit_message_text(text, c_id, m_id, reply_markup=mk)
    else: 
        s = bot.send_message(c_id, text, reply_markup=mk)
        if u_id: last_menus[u_id] = s.message_id

def show_settings_menu(c_id, m_id):
    s = get_settings(); fj = "✅ ON" if s['force_join'] else "❌ OFF"
    text = (f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} <b>BOT SETTINGS CENTER</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"Force Join: <b>{fj}</b>\n"
            f"Brand: <b>{s['brand_name']}</b>\n"
            f"Mask: <b>{s['mask_text']}</b>")
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton(f"Force Join: {fj}", callback_data="toggle_fj"))
    mk.add(types.InlineKeyboardButton("📢 Channels", callback_data="m_chan"), types.InlineKeyboardButton("👥 Admins", callback_data="m_adm"))
    mk.add(types.InlineKeyboardButton("💬 OTP Groups", callback_data="m_grp"), types.InlineKeyboardButton("✨ UI Style", callback_data="m_style"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_adm"))
    bot.edit_message_text(text, c_id, m_id, reply_markup=mk)

# ==========================================
# 📡 OTP ENGINE (SYNC WITH server.ts)
# ==========================================
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
                    
                    # Logic: OTP Body Change Check
                    otp_m = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                    code = otp_m.group(0) if otp_m else content
                    
                    if last_number_otp.get(norm) == code:
                        processed_messages.add(mid); continue
                    
                    last_number_otp[norm] = code; processed_messages.add(mid)
                    
                    # Formatting Mirror
                    icon_d = APP_EMOJIS.get(osrv.upper().replace(' ', ''))
                    icon = e(icon_d[0], icon_d[1]) if icon_d else e("🖥", "5337302974806922068")
                    
                    text = (f"━━━━━━━━━━━\n"
                            f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} <b>𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘</b> 》\n"
                            f"━━━━━━━━━━━\n"
                            f"<blockquote>{e('🔹', PREMIUM_EMOJIS['DOT'])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>{osrv}</b></blockquote>\n"
                            f"<blockquote>{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>{norm}</code></blockquote>\n"
                            f"━━━━━━━━━━━\n"
                            f"<blockquote>{e('💬', PREMIUM_EMOJIS['FIRE'])} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>{content}</code></blockquote>\n"
                            f"━━━━━━━━━━━\n"
                            f"<i>{sets.get('brand_name', 'DXA UNIVERSE')}</i>")
                    
                    markup = json.dumps({"inline_keyboard": [[{"text": f"📋 {code}", "copy_text": {"text": code}}]]})
                    for g_id in sets.get("otp_groups", []):
                        try: bot.send_message(g_id, text, reply_markup=markup); except: pass
                    match = next((n for n in nums if n.get('used') and re.sub(r'\D', '', str(n['number'])) == norm), None)
                    if match:
                        try: bot.send_message(match['assignedTo'], text, reply_markup=markup); except: pass
            time.sleep(5)
        except: time.sleep(10)

# ==========================================
# 📢 BROADCAST & 📤 UPLOAD LOGIC
# ==========================================
def do_bc(msg, sid):
    if msg.text and msg.text.startswith('/'): return
    users = read_json("users.json")
    status = bot.send_message(msg.chat.id, f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} <b>Broadcasting...</b>\n0/{len(users)}")
    ok = 0
    for i, u in enumerate(users):
        try: bot.copy_message(u['uid'], msg.chat.id, msg.message_id); ok += 1
        except: pass
        if (i+1)%10 == 0 or i == len(users)-1:
            try: bot.edit_message_text(f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} <b>Broadcasting...</b>\nProgress: {i+1}/{len(users)}\nSuccess: {ok}", msg.chat.id, status.message_id); except: pass
    bot.edit_message_text(f"{e('✅', PREMIUM_EMOJIS['DONE'])} <b>Broadcast Over!</b> Success: {ok}", msg.chat.id, status.message_id)

def do_up(msg, sid):
    if not msg.document: bot.send_message(msg.chat.id, "❌ Error: Send a .txt file."); return
    # Sequential input for service/country mirror...
    bot.send_message(msg.chat.id, f"✅ File received: {msg.document.file_name}. Processing sub-data...")

# ==========================================
# 🕹️ CALLBACKS & COMMANDS
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def router(call):
    u_id, c_id, d = call.from_user.id, call.message.chat.id, call.data
    
    if d == "back_adm": show_admin_panel(c_id, call.message.message_id)
    elif d == "adm_sets": show_settings_menu(c_id, call.message.message_id)
    elif d == "toggle_fj":
        s = get_settings(); s['force_join'] = not s['force_join']; write_json("settings.json", s); router(call)
    elif d == "adm_bc":
        bot.edit_message_text("📢 Send ANY message (Media supported):", c_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Back", callback_data="back_adm")))
        bot.register_next_step_handler(call.message, do_bc, call.message.message_id)
    elif d == "adm_up":
        bot.edit_message_text("📤 <b>UPLOAD</b>\n━━━━━━━━━━\nSend .txt file:", c_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Back", callback_data="back_adm")))
        bot.register_next_step_handler(call.message, do_up, call.message.message_id)
    elif d == "close":
        bot.clear_step_handler_by_chat_id(c_id)
        try: bot.delete_message(c_id, call.message.message_id); except: pass
    elif d == "m_chan":
        # Channel management view here ...
        pass

@bot.message_handler(commands=['start'])
def start(m):
    u_id = m.from_user.id; users = read_json("users.json")
    if not any(u['uid'] == str(u_id) for u in users):
        users.append({'uid': str(u_id), 'username': m.from_user.username, 'time': str(datetime.now())})
        write_json("users.json", users)
    delete_last_menu(m.chat.id, u_id)
    if not check_join(u_id):
        settings = get_settings(); markup = types.InlineKeyboardMarkup()
        for c in settings['channels']: markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="check_join_trigger"))
        bot.send_message(m.chat.id, f"{e('🚫', PREMIUM_EMOJIS['CLOSE'])} <b>Access Restricted!</b>\nJoin channel first.", reply_markup=markup)
        return
    bot.send_message(m.chat.id, f"Welcome!", reply_markup=get_main_keyboard(u_id))

@bot.message_handler(func=lambda m: True)
def text_router(m):
    u_id = m.from_user.id
    if not check_join(u_id): return
    if m.text == "👑 Admin Panel" and is_admin(u_id): show_admin_panel(m.chat.id, u_id=u_id)
    elif m.text == "📱 Get Number":
        # Full service allocation logic here ...
        pass

if __name__ == "__main__":
    threading.Thread(target=fetch_otps, daemon=True).start()
    bot.infinity_polling()
