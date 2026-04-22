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
    'TELEGRAM': ['🚫', '5337010556253543833'], 'BKASH': ['💸', '5348469219761626211'],
    'NAGAD': ['💴', '5352985330628730418'], 'INSTAGRAM': ['🚫', '5334868205091459431'],
    'ROCKET_APP': ['💸', '5346042941196507141'], 'BINANCE': ['💸', '5348212415077064131']
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

def settings():
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
            "otp_message_buttons": []
        }
        write_db("settings.json", s)
    return s

def is_admin(uid):
    s = settings()
    return uid == ADMIN_ID or str(uid) in s["admins"]

# ==========================================
# 📊 OTP MONITORING ENGINE
# ==========================================
processed_otps = set()
last_codes = {}

def otp_monitor_task():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=100", timeout=8)
            if res.status_code == 200:
                data = res.json()
                nums = read_db("numbers.json")
                s = settings()
                for rec in data:
                    service, num_f, content, ts = rec
                    mid = f"{num_f}_{ts}"
                    if mid in processed_otps: continue
                    
                    # Logic: Extract Code
                    codes = re.findall(r'\d{4,8}', content)
                    code = codes[0] if codes else content
                    norm_num = "".join(filter(str.isdigit, num_f))
                    
                    if last_codes.get(norm_num) == code:
                        processed_otps.add(mid)
                        continue
                        
                    last_codes[norm_num] = code
                    processed_otps.add(mid)
                    
                    # Formatting
                    brand = s.get("brand_name", "DXA UNIVERSE")
                    mask = s.get("mask_text", "DXA")
                    masked = f"{norm_num[:3]}{mask}{norm_num[-4:]}" if len(norm_num) > 7 else norm_num
                    
                    s_key = service.upper().replace(" ", "")
                    icon_cfg = APP_EMOJIS.get(s_key, ['🖱', PREMIUM_EMOJIS["DOT"]])
                    
                    msg = (
                        f"━━━━━━━━━━━\n"
                        f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 》\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e(icon_cfg[0], icon_cfg[1])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>{service}</b></blockquote>\n"
                        f"<blockquote>{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>{masked}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>{content}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<i>{brand}</i>"
                    )
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(f"📋 Copy Code: {code}", callback_data="copy"))
                    for b in s.get("otp_message_buttons", []):
                        markup.add(types.InlineKeyboardButton(b["text"], url=b["url"]))
                    
                    # Send to Groups
                    for gid in s.get("otp_groups", []):
                        try: bot.send_message(gid, msg, reply_markup=markup)
                        except: pass
                        
                    # Send to Private User
                    match = next((n for n in nums if n.get("used") and "".join(filter(str.isdigit, str(n["number"]))).endswith(norm_num[-8:])), None)
                    if match:
                        try: bot.send_message(match["assignedTo"], msg, reply_markup=markup)
                        except: pass
        except: pass
        time.sleep(4)

threading.Thread(target=otp_monitor_task, daemon=True).start()

# ==========================================
# 🛡️ MIDDLEWARES
# ==========================================
def check_join(uid):
    s = settings()
    if not s["force_join"] or is_admin(uid): return True
    for c in s["channels"]:
        try:
            m = bot.get_chat_member(c["username"], uid)
            if m.status in ['left', 'kicked', 'restricted']: return False
        except: return False
    return True

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 Get Number", "🛠 Support")
    if is_admin(uid): kb.row("👑 Admin Panel")
    return kb

# ==========================================
# 👑 ADMIN SYSTEM (MULTI-LEVEL)
# ==========================================

def admin_panel_ui(cid, mid=None):
    users, nums = read_db("users.json"), read_db("numbers.json")
    free = len([n for n in nums if not n.get("used")])
    total = len(nums) or 1
    bar_size = int((free/total)*10)
    bar = "█"*bar_size + "░"*(10-bar_size)
    
    txt = (
        f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>DXA ADMIN CONSOLE</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{e('👤', PREMIUM_EMOJIS['USER'])} Users: {len(users)}\n"
        f"{e('🔢', PREMIUM_EMOJIS['NUMBERS'])} Total Stock: {len(nums)}\n"
        f"{e('🚀', PREMIUM_EMOJIS['ROCKET'])} Available: {free}\n\n"
        f"<b>Inventory:</b>\n[{bar}] {free} Left\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload", callback_data="adm_up"), types.InlineKeyboardButton("🗑 Files", callback_data="adm_fs"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"), types.InlineKeyboardButton("⚙️ Settings", callback_data="adm_sets"))
    markup.add(types.InlineKeyboardButton("✅ Used Stock", callback_data="view_used"), types.InlineKeyboardButton("❌ Clear Unused", callback_data="clear_unused"))
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="cls"))
    
    if mid: bot.edit_message_text(txt, cid, mid, reply_markup=markup)
    else: bot.send_message(cid, txt, reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data.startswith("adm_"))
def admin_callbacks(q):
    uid, cid, mid, data = q.from_user.id, q.message.chat.id, q.message.message_id, q.data
    if not is_admin(uid): return
    
    if data == "adm_sets":
        s = settings()
        fj_stat = "Active ✅" if s["force_join"] else "Disabled ❌"
        txt = f"⚙️ <b>GLOBAL SETTINGS</b>\n━━━━━━━━━━━━━\nFJ Status: {fj_stat}\nChannels: {len(s['channels'])}\nAdmins: {len(s['admins'])}\nGroups: {len(s['otp_groups'])}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Channel Manage", callback_data="m_chan"), types.InlineKeyboardButton("👥 Admin Manage", callback_data="m_adm"))
        markup.add(types.InlineKeyboardButton("💬 Group Manage", callback_data="m_grp"), types.InlineKeyboardButton("🔍 Branding", callback_data="m_brand"))
        markup.add(types.InlineKeyboardButton(f"Toggle FJ: {'OFF' if s['force_join'] else 'ON'}", callback_data="tog_fj"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_main"))
        bot.edit_message_text(txt, cid, mid, reply_markup=markup)

    elif data == "adm_main": admin_panel_ui(cid, mid)
    
    elif data == "adm_bc":
        bot.send_message(cid, f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} Send message to broadcast:")
        bot.register_next_step_handler(q.message, broadcast_engine)

def broadcast_engine(msg):
    users = read_db("users.json")
    bot.send_message(msg.chat.id, f"🚀 Sending to {len(users)} users...")
    success, fail = 0, 0
    for u in users:
        try:
            bot.copy_message(u["uid"], msg.chat.id, msg.message_id)
            success += 1
        except: fail += 1
    bot.send_message(msg.chat.id, f"✅ Done!\nSuccess: {success}\nFail: {fail}")

# ==========================================
# 📱 USER SYSTEM & ALLOCATION
# ==========================================

@bot.message_handler(commands=['start'])
def handle_start(msg):
    uid = msg.from_user.id
    if not check_join(uid):
        s = settings()
        markup = types.InlineKeyboardMarkup()
        for c in s["channels"]: markup.add(types.InlineKeyboardButton(f"Join: {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="verify_join"))
        return bot.send_message(uid, f"{e('🚫', PREMIUM_EMOJIS['CLOSE'])} <b>JOIN REQUIRED</b>", reply_markup=markup)
    
    users = read_db("users.json")
    if not any(str(u['uid']) == str(uid) for u in users):
        users.append({"uid": str(uid), "user": msg.from_user.username, "date": str(datetime.now())})
        write_db("users.json", users)
    
    bot.send_message(uid, f"{e('🔥', PREMIUM_EMOJIS['FIRE'])} <b>DXA BOT ONLINE</b>", reply_markup=main_kb(uid))

@bot.message_handler(func=lambda m: m.text == "📱 Get Number")
def request_number(msg):
    if not check_join(msg.from_user.id): return
    nums = read_db("numbers.json")
    services = sorted(list(set([n["service"] for n in nums if not n.get("used")])))
    
    if not services:
        return bot.send_message(msg.chat.id, "❌ Stock empty! Please wait for update.")
        
    markup = types.InlineKeyboardMarkup()
    for s in services: markup.add(types.InlineKeyboardButton(f"🔹 {s}", callback_data=f"usr_svc:{s}"))
    bot.send_message(msg.chat.id, "📱 <b>Select Your Service:</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data.startswith("usr_svc:"))
def select_country(q):
    svc = q.data.split(":")[1]
    nums = read_db("numbers.json")
    countries = sorted(list(set([n["country"] for n in nums if not n.get("used") and n["service"] == svc])))
    
    markup = types.InlineKeyboardMarkup()
    for c in countries: markup.add(types.InlineKeyboardButton(f"📍 {c}", callback_data=f"usr_cnt:{svc}:{c}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="usr_back_svc"))
    bot.edit_message_text(f"📍 <b>Select Country for {svc}:</b>", q.message.chat.id, q.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda q: q.data.startswith("usr_cnt:"))
def allocate_numbers(q):
    _, svc, cnt = q.data.split(":")
    all_num = read_db("numbers.json")
    available = [n for n in all_num if not n.get("used") and n["service"] == svc and n["country"] == cnt]
    
    if len(available) < 3:
        return bot.answer_callback_query(q.id, "❌ Not enough stock for this country!", show_alert=True)
    
    selected = random.sample(available, 3)
    sel_ids = [n["id"] for n in selected]
    
    for n in all_num:
        if n["id"] in sel_ids:
            n["used"] = True
            n["assignedTo"] = q.from_user.id
            n["assignedAt"] = str(datetime.now())
            
    write_db("numbers.json", all_num)
    
    icons = [e("1️⃣", PREMIUM_EMOJIS["N1"]), e("2️⃣", PREMIUM_EMOJIS["N2"]), e("3️⃣", PREMIUM_EMOJIS["N3"])]
    num_list = "\n".join([f"{icons[i]} <code>{n['number']}</code>" for i, n in enumerate(selected)])
    
    text = (
        f"━━━━━━━━━━━\n"
        f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗨𝗠𝗕𝗘𝗥𝗦 𝗔𝗟𝗟𝗢𝗖𝗔𝗧𝗘𝗗 》\n"
        f"━━━━━━━━━━━\n"
        f"<b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> {svc}\n"
        f"<b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {cnt}\n"
        f"━━━━━━━━━━━\n"
        f"{num_list}\n"
        f"━━━━━━━━━━━\n"
        f"<i>Wait for OTP in our group or here.</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Join OTP Group", url=settings()["otp_link"]))
    bot.edit_message_text(text, q.message.chat.id, q.message.message_id, reply_markup=markup)

# ==========================================
# 📂 FILE UPLOAD & PROCESSING
# ==========================================

@bot.callback_query_handler(func=lambda q: q.data == "adm_up")
def upload_prompt(q):
    bot.send_message(q.message.chat.id, f"{e('📤', PREMIUM_EMOJIS['UPLOAD'])} Send .txt file.\nFormat: <code>Number|Service|Country</code>")
    bot.register_next_step_handler(q.message, file_handler)

def file_handler(msg):
    if not msg.document: return bot.send_message(msg.chat.id, "❌ Please send a file!")
    
    status = bot.send_message(msg.chat.id, f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} Processing...")
    finfo = bot.get_file(msg.document.file_id)
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{finfo.file_path}"
    
    raw = requests.get(url).text
    lines = [L.strip() for L in raw.splitlines() if L.strip()]
    
    nums = read_db("numbers.json")
    files = read_db("files.json")
    added = 0
    
    for L in lines:
        p = L.split("|")
        if len(p) == 3:
            nums.append({
                "id": random.randint(100000, 999999),
                "number": p[0], "service": p[1], "country": p[2],
                "used": False, "createdAt": str(datetime.now())
            })
            added += 1
            
    files.append({"name": msg.document.file_name, "count": added, "date": str(datetime.now())})
    write_db("numbers.json", nums)
    write_db("files.json", files)
    
    bot.edit_message_text(f"✅ Successfully added {added} numbers from {msg.document.file_name}", msg.chat.id, status.message_id)

# General Callbacks
@bot.callback_query_handler(func=lambda q: q.data == "cls")
def close_h(q): bot.delete_message(q.message.chat.id, q.message.message_id)

@bot.callback_query_handler(func=lambda q: q.data == "verify_join")
def verify_h(q):
    if check_join(q.from_user.id):
        bot.delete_message(q.message.chat.id, q.message.message_id)
        bot.send_message(q.from_user.id, "✅ Access Granted!", reply_markup=main_kb(q.from_user.id))
    else: bot.answer_callback_query(q.id, "❌ You still haven't joined!", show_alert=True)

print("number_bot.py is now fully loaded with 1:1 systems.")
bot.infinity_polling()
