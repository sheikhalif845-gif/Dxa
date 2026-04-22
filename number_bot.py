import telebot
import requests
import json
import os
import time
import threading
import random
from telebot import types
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
BOT_TOKEN = "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg"
ADMIN_ID = 8197284774
OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats"
OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ=="

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ==========================================
# 🎨 PREMIUM UI ASSETS
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
    "DATE": "5352585194295564660", "WARN": "5336944168944047463", "SETTINGS": "5420155432272438703"
}

APP_EMOJIS = {
    'FACEBOOK': ['🚫', '5334807341109908955'], 'WHATSAPP': ['🚫', '5334759662677957452'],
    'TELEGRAM': ['🚫', '5337010556253543833'], 'BKASH': ['💸', '5348469219761626211'],
    'NAGAD': ['💴', '5352985330628730418'], 'INSTAGRAM': ['🚫', '5334868205091459431']
}

def e(emoji, eid):
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# ==========================================
# 📂 DATA SYSTEM
# ==========================================
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def read_db(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path): return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return []

def write_db(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
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
processed_msgs = set()
last_otp_codes = {}

def otp_monitor_task():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50", timeout=10)
            if res.status_code == 200:
                data = res.json()
                all_nums = read_db("numbers.json")
                settings = get_settings()
                
                for rec in data:
                    if len(rec) < 4: continue
                    service, full_num, content, timestamp = rec
                    norm_num = "".join(filter(str.isdigit, full_num))
                    msg_id = f"{full_num}_{timestamp}"
                    
                    if msg_id in processed_msgs: continue
                    
                    # Extract OTP
                    import re
                    otp_codes = re.findall(r'\d{4,8}', content)
                    code = otp_codes[0] if otp_codes else content
                    
                    if last_otp_codes.get(norm_num) == code:
                        processed_msgs.add(msg_id)
                        continue
                        
                    last_otp_codes[norm_num] = code
                    processed_msgs.add(msg_id)
                    
                    # UI Formatting
                    brand = settings.get("brand_name", "DXA UNIVERSE")
                    mask = settings.get("mask_text", "DXA")
                    masked = f"{norm_num[:3]}{mask}{norm_num[-4:]}" if len(norm_num) > 7 else norm_num
                    
                    s_key = service.upper().replace(" ", "")
                    icon_data = APP_EMOJIS.get(s_key, ['🖱', PREMIUM_EMOJIS["DOT"]])
                    s_icon = e(icon_data[0], icon_data[1])
                    
                    msg_text = (
                        f"━━━━━━━━━━━\n"
                        f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 》\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e('🔹', PREMIUM_EMOJIS['DOT'])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>{service}</b></blockquote>\n"
                        f"<blockquote>{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>{masked}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<blockquote>{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>{content}</code></blockquote>\n"
                        f"━━━━━━━━━━━\n"
                        f"<i>{brand}</i>"
                    )
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(f"📋 {code}", callback_data="copy"))
                    for btn in settings.get("otp_message_buttons", []):
                        markup.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
                        
                    # Forward to groups
                    for gid in settings.get("otp_groups", []):
                        try: bot.send_message(gid, msg_text, reply_markup=markup)
                        except: pass
                        
                    # Send to user
                    match = next((n for n in all_nums if n.get("used") and "".join(filter(str.isdigit, str(n["number"]))) == norm_num), None)
                    if match:
                        try: bot.send_message(match["assignedTo"], msg_text, reply_markup=markup)
                        except: pass
                        
        except Exception as err:
            print(f"Monitor error: {err}")
        time.sleep(5)

threading.Thread(target=otp_monitor_task, daemon=True).start()

# ==========================================
# 🛡️ SYSTEM HELPERS
# ==========================================
def check_join(uid):
    s = get_settings()
    if not s.get("force_join") or is_admin(uid): return True
    for c in s.get("channels", []):
        try:
            m = bot.get_chat_member(c["username"], uid)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

def get_main_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 Get Number", "🛠 Support")
    if is_admin(uid): kb.row("👑 Admin Panel")
    return kb

# ==========================================
# 🤖 BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    if not check_join(uid):
        s = get_settings()
        text = f"{e('🚫', PREMIUM_EMOJIS['CLOSE'])} <b>ACCESS RESTRICTED</b>\nJoin our channels to unlock access!"
        markup = types.InlineKeyboardMarkup()
        for c in s.get("channels", []):
            markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="check_join"))
        return bot.send_message(uid, text, reply_markup=markup)
    
    # Register user
    users = read_db("users.json")
    if not any(u['uid'] == str(uid) for u in users):
        users.append({"uid": str(uid), "joinedAt": str(datetime.now())})
        write_db("users.json", users)
        
    welcome = (
        f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗡𝗨𝗠𝗕𝗘𝗥 𝗕𝗢𝗧 》═\n"
        f"━━━━━━━━━━━\n"
        f"{e('👋', PREMIUM_EMOJIS['HELLO'])} Welcome <b>{msg.from_user.first_name}</b>!\n"
        f"Ready to generate numbers.\n"
        f"━━━━━━━━━━━"
    )
    bot.send_message(uid, welcome, reply_markup=get_main_menu(uid))

@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def admin_panel(msg):
    uid = msg.from_user.id
    if not is_admin(uid): return
    
    nums = read_db("numbers.json")
    users = read_db("users.json")
    free = len([n for n in nums if not n.get("used")])
    total = len(nums) or 1
    percent = int((free / total) * 10)
    bar = "█" * percent + "░" * (10 - percent)
    
    dash = (
        f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN DASHBOARD</b>\n"
        f"━━━━━━━━━━━━━\n"
        f"{e('👤', PREMIUM_EMOJIS['USER'])} Users: {len(users)}\n"
        f"{e('🔢', PREMIUM_EMOJIS['NUMBERS'])} Numbers: {len(nums)}\n"
        f"{e('🚀', PREMIUM_EMOJIS['ROCKET'])} Available: {free}\n"
        f"Stock: [{bar}]\n"
        f"━━━━━━━━━━━━━"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Upload", callback_data="adm_up"), types.InlineKeyboardButton("🗑 Files", callback_data="adm_fs"))
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"), types.InlineKeyboardButton("⚙️ Settings", callback_data="adm_sets"))
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="cls"))
    bot.send_message(uid, dash, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📱 Get Number")
def get_number_handler(msg):
    uid = msg.from_user.id
    if not check_join(uid): return
    
    nums = read_db("numbers.json")
    svcs = sorted(list(set([n["service"] for n in nums if not n.get("used")])))
    
    if not svcs:
        return bot.send_message(uid, "❌ No numbers available.")
        
    markup = types.InlineKeyboardMarkup()
    for s in svcs:
        markup.add(types.InlineKeyboardButton(f"🔹 {s}", callback_data=f"sel_s:{s}"))
    bot.send_message(uid, f"{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>Select Service:</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda q: True)
def calls(q):
    uid = q.from_user.id
    data = q.data
    mid = q.message.message_id
    
    if data == "cls": bot.delete_message(uid, mid)
    
    if data.startswith("sel_s:"):
        svc = data.split(":")[1]
        nums = read_db("numbers.json")
        available = [n for n in nums if not n.get("used") and n["service"] == svc]
        countries = sorted(list(set([n["country"] for n in available])))
        
        markup = types.InlineKeyboardMarkup()
        for c in countries:
            markup.add(types.InlineKeyboardButton(f"📍 {c}", callback_data=f"sel_c:{svc}:{c}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="cls"))
        bot.edit_message_text(f"📍 <b>Select Country for {svc}:</b>", uid, mid, reply_markup=markup)

    if data.startswith("sel_c:"):
        svc, country = data.split(":")[1], data.split(":")[2]
        nums = read_db("numbers.json")
        available = [n for n in nums if not n.get("used") and n["service"] == svc and n["country"] == country]
        
        if len(available) < 3:
            return bot.answer_callback_query(q.id, "❌ Not enough numbers!", show_alert=True)
            
        selected = random.sample(available, 3)
        sel_ids = [n["id"] for n in selected]
        
        for n in nums:
            if n["id"] in sel_ids:
                n["used"] = True
                n["assignedTo"] = uid
                n["assignedAt"] = str(datetime.now())
        
        write_db("numbers.json", nums)
        
        formatted = []
        icons = [e("1️⃣", PREMIUM_EMOJIS["N1"]), e("2️⃣", PREMIUM_EMOJIS["N2"]), e("3️⃣", PREMIUM_EMOJIS["N3"])]
        for i, n in enumerate(selected):
            num = str(n["number"])
            if not num.startswith("+"): num = "+" + num
            formatted.append(f"{icons[i]} <code>{num}</code>")
            
        text = (
            f"━━━━━━━━━━━\n"
            f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗨𝗠𝗕𝗘𝗥𝗦 𝗔𝗟𝗟𝗢𝗖𝗔𝗧𝗘𝗗 》\n"
            f"━━━━━━━━━━━\n"
            f"<b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> {svc}\n"
            f"<b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {country}\n"
            f"━━━━━━━━━━━\n"
            + "\n".join(formatted) + "\n"
            f"━━━━━━━━━━━\n"
            f"<i>Powered by DXA UNIVERSE</i>"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 OTP Group", url=get_settings()["otp_link"]))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="cls"))
        bot.edit_message_text(text, uid, mid, reply_markup=markup)

    # Admin actions
    if data == "adm_bc" and is_admin(uid):
        msg = bot.send_message(uid, "💬 Send message to broadcast:")
        bot.register_next_step_handler(msg, process_bc)

def process_bc(msg):
    uid = msg.from_user.id
    users = read_db("users.json")
    bot.send_message(uid, f"🚀 Broadcasting to {len(users)} users...")
    count = 0
    for u in users:
        try:
            bot.copy_message(u["uid"], uid, msg.message_id)
            count += 1
        except: pass
    bot.send_message(uid, f"✅ Broadcast done! Sent to {count} users.")

print("number_bot.py is running. App-like systems fully active.")
bot.infinity_polling()
