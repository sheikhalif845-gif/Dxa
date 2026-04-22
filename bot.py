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

def get_settings():
    s = read_json("settings.json")
    if not s or isinstance(s, list):
        s = {"force_join": True, "channels": [{"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}],
             "admins": [], "otp_groups": [], "otp_link": "https://t.me/dxaotpzone", "brand_name": "DXA UNIVERSE", "mask_text": "DXA"}
        write_json("settings.json", s)
    return s

def is_admin(uid):
    if str(uid) == str(ADMIN_ID): return True
    return str(uid) in [str(a) for a in get_settings().get("admins", [])]

# --- ASSETS (Mirroring App Design) ---
PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DONE": "5352694861990501856",
    "NUMBER": "5337132498965010628", "ADMIN": "5353032893096567467", "CLOSE": "5420130255174145507",
    "SETTINGS": "5420155432272438703", "DOT": "5352638632278660622", "PIN": "5420517437885943844"
}
def e(emoji, eid): return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# --- GLOBAL STATE ---
processed_messages = set(); last_number_otp = {}; last_menus = {}

# --- OTP PROCESSOR (Mirroring App Design) ---
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
                    
                    otp_m = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                    code = otp_m.group(0) if otp_m else content
                    if last_number_otp.get(norm) == code: processed_messages.add(mid); continue
                    
                    last_number_otp[norm] = code; processed_messages.add(mid)
                    
                    # дизайн (HTML Mirror)
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

# --- UI HANDLERS ---
def show_admin_panel(c_id, m_id=None, u_id=None):
    users = read_json("users.json"); nums = read_json("numbers.json")
    assigned = len([n for n in nums if n.get('used')]); total = len(nums); avail = total - assigned
    bar = "█" * int((avail/total)*10) if total > 0 else ""
    text = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN PANEL</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"Users: {len(users)} | Stock: {avail}/{total}\n"
            f"Power: [{bar.ljust(10, '░')}]\n"
            f"━━━━━━━━━━━━━")
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("📤 Upload", callback_data="admin_upload"), types.InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"))
    mk.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), types.InlineKeyboardButton("🗑 Delete Files", callback_data="admin_delete_files"))
    mk.add(types.InlineKeyboardButton("🔙 Close", callback_data="close_menu"))
    if m_id: bot.edit_message_text(text, c_id, m_id, reply_markup=mk)
    else: bot.send_message(c_id, text, reply_markup=mk)

@bot.callback_query_handler(func=lambda call: True)
def router(call):
    u_id, c_id, d = call.from_user.id, call.message.chat.id, call.data
    if d == "admin_panel_back": show_admin_panel(c_id, call.message.message_id)
    elif d == "admin_settings":
        s = get_settings(); fj = "✅ ON" if s['force_join'] else "❌ OFF"
        text = f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} <b>SETTINGS CENTER</b>\n━━━━━━━━━━━━━"
        mk = types.InlineKeyboardMarkup()
        mk.row(types.InlineKeyboardButton(f"Force Join: {fj}", callback_data="toggle_fj"))
        mk.row(types.InlineKeyboardButton("Channels", callback_data="m_chan"), types.InlineKeyboardButton("Admins", callback_data="m_adm"))
        mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back"))
        bot.edit_message_text(text, c_id, call.message.message_id, reply_markup=mk)
    elif d == "toggle_fj":
        s = get_settings(); s['force_join'] = not s['force_join']; write_json("settings.json", s); router(call)
    elif d == "admin_broadcast":
        bot.edit_message_text("📢 Send EVERYthing (Media Support):", c_id, call.message.message_id)
        bot.register_next_step_handler(call.message, do_bc, call.message.message_id)
    elif d == "close_menu": bot.delete_message(c_id, call.message.message_id)

def do_bc(m, status_id):
    users = read_json("users.json"); status = bot.send_message(m.chat.id, "⏳ <b>Broadcasting...</b>")
    ok = 0
    for i, u in enumerate(users):
        try: bot.copy_message(u['uid'], m.chat.id, m.message_id); ok += 1
        except: pass
        if (i+1)%10 == 0: bot.edit_message_text(f"⏳ Progress: {i+1}/{len(users)}", m.chat.id, status.message_id)
    bot.send_message(m.chat.id, f"✅ Broadcast sent to {ok} users.")

@bot.message_handler(commands=['start'])
def start(m):
    u_id = m.from_user.id; users = read_json("users.json")
    if not any(u['uid'] == str(u_id) for u in users): users.append({'uid': str(u_id)}); write_json("users.json", users)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.row("📱 Get Number", "🛠 Support")
    if is_admin(u_id): kb.row("👑 Admin Panel")
    bot.send_message(m.chat.id, f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗡𝗨𝗠𝗕𝗘𝗥 𝗕𝗢𝗧 》═", reply_markup=kb)

if __name__ == "__main__":
    threading.Thread(target=fetch_otps, daemon=True).start()
    bot.infinity_polling()
