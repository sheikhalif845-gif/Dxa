import telebot
import requests
import json
import os
import time
import threading
import random
from telebot import types
from datetime import datetime

# --- Configuration ---
BOT_TOKEN = "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg"
ADMIN_ID = 8197284774
OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats"
OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ=="

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- Assets & UI ---
PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "ADMIN": "5353032893096567467",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "GRAPH": "5352877703043258544",
    "DOT": "5352638632278660622", "WAIT": "5336983442125001376"
}

def e(emoji, eid): return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# --- Data Store ---
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def db_get(file):
    if not os.path.exists(os.path.join(DATA_DIR, file)): return []
    with open(os.path.join(DATA_DIR, file), 'r') as f: return json.load(f)

def db_put(file, data):
    with open(os.path.join(DATA_DIR, file), 'w') as f: json.dump(data, f, indent=2)

def settings():
    s = db_get("settings.json")
    if not s or isinstance(s, list):
        s = {"force_join": True, "channels": [], "admins": [], "otp_groups": [], "otp_link": "https://t.me/dxaotpzone"}
        db_put("settings.json", s)
    return s

# --- Middlewares ---
def is_admin(uid): return uid == ADMIN_ID or str(uid) in settings()["admins"]

def check_join(uid):
    s = settings()
    if not s["force_join"] or is_admin(uid): return True
    for c in s["channels"]:
        try:
            m = bot.get_chat_member(c["username"], uid)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

# --- UI Functions ---
def adm_panel(cid, mid=None):
    nums = db_get("numbers.json")
    usrs = db_get("users.json")
    free = len([n for n in nums if not n.get("used")])
    text = f"{e('👑', PREMIUM_EMOJIS['ADMIN'])} <b>ADMIN DASHBOARD</b>\n\nUsers: {len(usrs)}\nFree Numbers: {free}"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📢 Broadcast", callback_data="bc"), types.InlineKeyboardButton("⚙️ Settings", callback_data="sets"))
    if mid: bot.edit_message_text(text, cid, mid, reply_markup=markup)
    else: bot.send_message(cid, text, reply_markup=markup)

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start_h(msg):
    uid = msg.from_user.id
    if not check_join(uid):
        s = settings()
        markup = types.InlineKeyboardMarkup()
        for c in s["channels"]: markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
        markup.add(types.InlineKeyboardButton("Joined ✅", callback_data="check"))
        return bot.send_message(uid, "🚫 Join our channels first!", reply_markup=markup)
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 Get Number", "🛠 Support")
    if is_admin(uid): kb.row("👑 Admin Panel")
    bot.send_message(uid, f"{e('🔥', PREMIUM_EMOJIS['FIRE'])} Welcome!", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def adm_h(m):
    if is_admin(m.from_user.id): adm_panel(m.chat.id)

@bot.callback_query_handler(func=lambda q: True)
def calls(q):
    cid, mid, uid, data = q.message.chat.id, q.message.message_id, q.from_user.id, q.data
    
    if data == "sets" and is_admin(uid):
        s = settings()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Toggle Force Join", callback_data="tog"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text("⚙️ <b>Settings Panel</b>", cid, mid, reply_markup=markup)

    if data == "bc" and is_admin(uid):
        msg = bot.send_message(cid, "📢 Send message to broadcast:")
        bot.register_next_step_handler(msg, bc_task)

    if data == "back": adm_panel(cid, mid)

def bc_task(msg):
    usrs = db_get("users.json")
    for u in usrs:
        try: bot.copy_message(u["uid"], msg.chat.id, msg.message_id)
        except: pass
    bot.send_message(msg.chat.id, "✅ Broadcast Complete!")

# --- OTP Engine ---
def otp_loop():
    seen = set()
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50").json()
            nums = db_get("numbers.json")
            for r in res:
                key = f"{r[1]}_{r[3]}"
                if key in seen: continue
                seen.add(key)
                m = next((n for n in nums if n.get("used") and "".join(filter(str.isdigit, r[1])).endswith(str(n['number']))), None)
                if m: bot.send_message(m["assignedTo"], f"📩 <b>New OTP:</b> <code>{r[2]}</code>")
        except: pass
        time.sleep(5)

threading.Thread(target=otp_loop, daemon=True).start()
bot.infinity_polling()
