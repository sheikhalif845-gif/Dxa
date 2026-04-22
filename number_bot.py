import telebot
import requests
import json
import os
import time
import threading
import random
import re
from telebot import types
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION & ENV
# ==========================================
BOT_TOKEN = "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg"
ADMIN_ID = 8197284774
OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats"
OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ=="

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ==========================================
# 🎨 PREMIUM UI ASSETS (SYNC WITH SERVER.TS)
# ==========================================
PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DXA": "5334763399299506604",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "SUPPORT": "5337302974806922068",
    "ADMIN": "5353032893096567467", "USER": "5352861489541714456", "FILE": "5352721946054268944",
    "NUMBERS": "5352862640592949843", "ROCKET": "5352597830089347330", "GRAPH": "5352877703043258544",
    "UPLOAD": "5353001161878182134", "BROADCAST": "5352980533150259581", "PIN": "5420517437885943844",
    "DOT": "5352638632278660622", "N1": "5352651766288652742", "N2": "5355186458418257716",
    "N3": "5352867219028091093", "WAIT": "5336983442125001376", "CLOSE": "5420130255174145507",
    "OTP_ID": "5353022963132174959", "OFF": "5352974971167611327", "NOTE": "5395444784611480792",
    "DATE": "5352585194295564660", "WARN": "5336944168944047463", "SETTINGS": "5420155432272438703",
    "CHAT": "5337302974806922068", "MEMBER": "5420145051336485498", "ADD": "5420323438508155202",
    "DELETE": "5422557736330106570"
}

APP_EMOJIS = {
    'FACEBOOK': ['🚫', '5334807341109908955'], 'WHATSAPP': ['🚫', '5334759662677957452'],
    'TELEGRAM': ['🚫', '5337010556253543833'], 'WHATSAPPBUSINESSES': ['🚫', '5336814486701514414'],
    'IMO': ['🚫', '5337155807752524558'], 'INSTAGRAM': ['🚫', '5334868205091459431'],
    'BKASH': ['💸', '5348469219761626211'], 'NAGAD': ['💴', '5352985330628730418'],
}

def e(emoji, eid): return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# ==========================================
# 🛠 DATA SYSTEM
# ==========================================
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def read_db(file):
    path = os.path.join(DATA_DIR, file)
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def write_db(file, data):
    with open(os.path.join(DATA_DIR, file), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_settings():
    s = read_db("settings.json")
    if not s or isinstance(s, list):
        s = {
            "force_join": True,
            "channels": [{"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}],
            "admins": [],
            "otp_groups": [],
            "otp_link": "https://t.me/dxaotpzone",
            "brand_name": "DXA UNIVERSE",
            "mask_text": "DXA",
            "group_buttons": {},
            "otp_message_buttons": []
        }
        write_db("settings.json", s)
    return s

def is_admin(uid):
    s = get_settings()
    return uid == ADMIN_ID or str(uid) in s["admins"]

# ==========================================
# 📊 OTP MONITORING ENGINE
# ==========================================
processed_otps = set()
last_codes = {}

def otp_monitor_task():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50", timeout=8)
            if res.status_code == 200:
                data = res.json()
                nums = read_db("numbers.json")
                s = get_settings()
                for rec in data:
                    srv, num_f, content, ts = rec
                    mid = f"{num_f}_{ts}"
                    if mid in processed_otps: continue
                    
                    codes = re.findall(r'\d{4,8}', content)
                    code = codes[0] if codes else content
                    norm = "".join(filter(str.isdigit, num_f))
                    
                    if last_codes.get(norm) == code:
                        processed_otps.add(mid)
                        continue
                        
                    last_codes[norm] = code
                    processed_otps.add(mid)
                    
                    brand = s.get("brand_name", "DXA UNIVERSE")
                    mask = s.get("mask_text", "DXA")
                    masked = f"{norm[:3]}{mask}{norm[-4:]}" if len(norm) > 7 else norm
                    
                    msg = (
                        f"━━━━━━━━━━━\n"
                        f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 》\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e('🔹', PREMIUM_EMOJIS['DOT'])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>{srv}</b></blockquote>\n"
                        f"<blockquote>{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>{masked}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>{content}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<i>{brand}</i>"
                    )
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(f"📋 {code}", callback_data="copy"))
                    for b in s.get("otp_message_buttons", []):
                        markup.add(types.InlineKeyboardButton(b["text"], url=b["url"]))
                    
                    for gid in s.get("otp_groups", []):
                        try: bot.send_message(gid, msg, reply_markup=markup)
                        except: pass
                        
                    match = next((n for n in nums if n.get("used") and "".join(filter(str.isdigit, str(n["number"]))).endswith(norm)), None)
                    if match:
                        try: bot.send_message(match["assignedTo"], msg, reply_markup=markup)
                        except: pass
        except: pass
        time.sleep(5)

threading.Thread(target=otp_monitor_task, daemon=True).start()

# ==========================================
# 🛡️ FORCE JOIN & HELPERS
# ==========================================
def check_join(uid):
    s = get_settings()
    if not s["force_join"] or is_admin(uid): return True
    for c in s["channels"]:
        try:
            m = bot.get_chat_member(c["username"], uid)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 Get Number", "🛠 Support")
    if is_admin(uid): kb.row("👑 Admin Panel")
    return kb

# ==========================================
# 🤖 BOT HANDLERS & ADMIN SYSTEM
# ==========================================
@bot.message_handler(commands=['start'])
def start_h(msg):
    uid = msg.from_user.id
    if not check_join(uid):
        s = get_settings()
        markup = types.InlineKeyboardMarkup()
        for c in s["channels"]: markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="check"))
        return bot.send_message(uid, "🚫 Join our channels first!", reply_markup=markup)
    
    users = read_db("users.json")
    if not any(u['uid'] == str(uid) for u in users):
        users.append({"uid": str(uid), "joinedAt": str(datetime.now())})
        write_db("users.json", users)
    
    bot.send_message(uid, f"{e('🔥', PREMIUM_EMOJIS['FIRE'])} <b>DXA BOT ACTIVE</b>", reply_markup=main_kb(uid))

@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel" and is_admin(m.from_user.id))
def admin_dash(m):
    nums, users = read_db("numbers.json"), read_db("users.json")
    free = len([n for n in nums if not n.get("used")])
    txt = (f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN PANEL</b>\n━━━━━━━━━━━━━\n"
           f"Users: {len(users)}\nNumbers: {len(nums)}\nAvailable: {free}")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload", callback_data="up"), types.InlineKeyboardButton("🗑 Files", callback_data="fs"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="bc"), types.InlineKeyboardButton("⚙️ Settings", callback_data="sets"))
    bot.send_message(m.chat.id, txt, reply_markup=markup)

# Sub-menu Handlers
@bot.callback_query_handler(func=lambda q: q.data == "sets")
def settings_h(q):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Force Join System", callback_data="m_fj"))
    markup.add(types.InlineKeyboardButton("👥 Admin Management", callback_data="m_adm"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_admin"))
    bot.edit_message_text("⚙️ <b>Settings Control</b>", q.message.chat.id, q.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data == "m_fj")
def manage_fj(q):
    s = get_settings()
    txt = f"Status: {'Active ✅' if s['force_join'] else 'Off ❌'}\nChannels: {len(s['channels'])}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Toggle ON/OFF", callback_data="tog_fj"))
    markup.add(types.InlineKeyboardButton("➕ Add Channel", callback_data="add_ch"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="sets"))
    bot.edit_message_text(txt, q.message.chat.id, q.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data == "tog_fj")
def tog_fj(q):
    s = get_settings()
    s["force_join"] = not s["force_join"]
    write_db("settings.json", s)
    bot.answer_callback_query(q.id, "Force Join Toggled!")
    manage_fj(q)

@bot.callback_query_handler(func=lambda q: q.data == "bc")
def bc_prompt(q):
    m = bot.send_message(q.message.chat.id, "📢 Send message to broadcast:")
    bot.register_next_step_handler(m, broadcast_job)

def broadcast_job(msg):
    users = read_db("users.json")
    bot.send_message(msg.chat.id, f"🚀 Broadcasting to {len(users)} users...")
    for u in users:
        try: bot.copy_message(u["uid"], msg.chat.id, msg.message_id)
        except: pass
    bot.send_message(msg.chat.id, "✅ Done!")

# File Processing
@bot.callback_query_handler(func=lambda q: q.data == "up")
def upload_prompt(q):
    m = bot.send_message(q.message.chat.id, "📤 Upload .txt file (Format: Number|Service|Country)")
    bot.register_next_step_handler(m, process_file)

def process_file(msg):
    if not msg.document: return bot.send_message(msg.chat.id, "❌ Not a document!")
    finfo = bot.get_file(msg.document.file_id)
    res = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{finfo.file_path}")
    lines = res.text.splitlines()
    
    nums = read_db("numbers.json")
    added = 0
    for l in lines:
        parts = l.split("|")
        if len(parts) == 3:
            nums.append({"id": random.randint(1000,9999), "number": parts[0], "service": parts[1], "country": parts[2], "used": False})
            added += 1
    write_db("numbers.json", nums)
    bot.send_message(msg.chat.id, f"✅ Added {added} numbers!")

@bot.message_handler(func=lambda m: m.text == "📱 Get Number")
def get_num(msg):
    nums = read_db("numbers.json")
    srvs = sorted(list(set([n["service"] for n in nums if not n.get("used")])))
    if not srvs: return bot.send_message(msg.chat.id, "❌ No numbers!")
    markup = types.InlineKeyboardMarkup()
    for s in srvs: markup.add(types.InlineKeyboardButton(s, callback_data=f"svc:{s}"))
    bot.send_message(msg.chat.id, "Select Service:", reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data.startswith("svc:"))
def sel_svc(q):
    svc = q.data.split(":")[1]
    nums = read_db("numbers.json")
    cnts = sorted(list(set([n["country"] for n in nums if not n.get("used") and n["service"] == svc])))
    markup = types.InlineKeyboardMarkup()
    for c in cnts: markup.add(types.InlineKeyboardButton(c, callback_data=f"cnt:{svc}:{c}"))
    bot.edit_message_text(f"Service: {svc}\nSelect Country:", q.message.chat.id, q.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data.startswith("cnt:"))
def allocate(q):
    _, svc, cnt = q.data.split(":")
    all = read_db("numbers.json")
    av = [n for n in all if not n.get("used") and n["service"] == svc and n["country"] == cnt]
    if len(av) < 3: return bot.answer_callback_query(q.id, "Not enough stock!", show_alert=True)
    sel = random.sample(av, 3)
    for n in sel: n["used"], n["assignedTo"] = True, q.from_user.id
    write_db("numbers.json", all)
    txt = f"✅ Success!\nService: {svc}\n" + "\n".join([f"<code>{n['number']}</code>" for n in sel])
    bot.edit_message_text(txt, q.message.chat.id, q.message.message_id)

bot.infinity_polling()
