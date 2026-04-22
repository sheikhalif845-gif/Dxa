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

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8197284774"))
OTP_API_URL = os.environ.get("OTP_API_URL", "http://147.135.212.197/crapi/st/viewstats")
OTP_API_TOKEN = os.environ.get("OTP_API_TOKEN", "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==")

if not BOT_TOKEN:
    print("❌ [TELEGRAM] BOT_TOKEN is missing or invalid. Please check your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

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
    'NAGAD': ('💴', '5352985330628730418')
}

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
    "DELETE": "5422557736330106570", "GIFT": "5420396762189831222", "PC": "5336879280578138635",
    "WEB": "5336972142066047577"
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

# --- Settings Management ---
def get_settings():
    settings = read_json("settings.json")
    if not settings or isinstance(settings, list):
        settings = {
            "force_join": True,
            "channels": [
                {"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}
            ],
            "admins": [],
            "otp_groups": [],
            "otp_link": "https://t.me/dxaotpzone",
            "brand_name": "DXA UNIVERSE",
            "mask_text": "DXA",
            "group_buttons": {}
        }
        write_json("settings.json", settings)
    
    # Schema Migration
    updated = False
    if "brand_name" not in settings:
        settings["brand_name"] = "DXA UNIVERSE"
        updated = True
    if "mask_text" not in settings:
        settings["mask_text"] = "DXA"
        updated = True
    if "group_buttons" not in settings:
        settings["group_buttons"] = {}
        updated = True
    if updated:
        write_json("settings.json", settings)
        
    return settings

def get_brand():
    return get_settings().get("brand_name", "DXA UNIVERSE")

def get_mask():
    return get_settings().get("mask_text", "DXA")

def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    settings = get_settings()
    return str(user_id) in [str(a) for a in settings.get("admins", [])]

def check_join(user_id):
    settings = get_settings()
    if not settings.get("force_join", True): return True
    if is_admin(user_id): return True
    
    for channel in settings.get("channels", []):
        try:
            member = bot.get_chat_member(channel['username'], user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

def show_force_join_msg(chat_id):
    settings = get_settings()
    text = (f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} <b>ACCESS RESTRICTED</b> {e('❌', PREMIUM_EMOJIS['CLOSE'])}\n"
            f"━━━━━━━━━━━━\n"
            f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} <b>Join Our Official Channel</b>\n\n"
            f"{e('🔐', PREMIUM_EMOJIS['OTP_ID'])} To unlock full access to <b>This Bot</b>, You Must Join Our Channel First.\n"
            f"━━━━━━━━━━━━\n"
            f"{e('✅', PREMIUM_EMOJIS['DONE'])} After Joining, Tap The Button Below To Continue")
    
    markup = types.InlineKeyboardMarkup()
    for c in settings.get("channels", []):
        markup.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c['url']))
    markup.add(types.InlineKeyboardButton(f"Joined {e('✅', PREMIUM_EMOJIS['DONE'])}", callback_data="check_join"))
    bot.send_message(chat_id, text, reply_markup=markup)

def delete_last_menu(chat_id, user_id):
    if user_id in last_menus:
        try: bot.delete_message(chat_id, last_menus[user_id])
        except: pass
        del last_menus[user_id]

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    markup.row("📱 Get Number", "🛠 Support")
    if is_admin(user_id):
        markup.row("👑 Menu Builder")
    return markup

# --- Service Views ---
def show_services(chat_id, message_id=None, user_id=None):
    numbers = read_json("numbers.json")
    available = [n for n in numbers if not n.get('used', False)]
    services = sorted(list(set([n['service'] for n in available])))
    
    markup = types.InlineKeyboardMarkup()
    if not services:
        text = f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} No numbers available at the moment."
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="close_menu"))
    else:
        text = f"{e('📱', PREMIUM_EMOJIS['NUMBER'])} <b>Select a Service:</b>"
        for s in services:
            markup.add(types.InlineKeyboardButton(f"{e('🔹', PREMIUM_EMOJIS['DOT'])} {s}", callback_data=f"sel_service:{s}"))
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="close_menu"))

    if message_id:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except: pass
    else:
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        if user_id: last_menus[user_id] = sent.message_id

def show_settings_panel(chat_id, message_id):
    text = (f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} <b>BOT SETTINGS CENTER</b> {e('⚙️', PREMIUM_EMOJIS['SETTINGS'])}\n"
            f"━━━━━━━━━━━━━\n\n"
            f"Welcome to the bot configuration hub. Select a category below to manage your bot instance.")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} Force Join System", callback_data="manage_force_join"))
    markup.row(types.InlineKeyboardButton(f"{e('👥', PREMIUM_EMOJIS['MEMBER'])} Admin Management", callback_data="manage_admins"))
    markup.row(types.InlineKeyboardButton(f"{e('💬', PREMIUM_EMOJIS['CHAT'])} OTP Group Management", callback_data="manage_otp_groups"))
    markup.row(types.InlineKeyboardButton(f"{e('🔗', PREMIUM_EMOJIS['PIN'])} Bot OTP Button Link", callback_data="manage_bot_otp_link"))
    markup.row(types.InlineKeyboardButton(f"{e('✨', PREMIUM_EMOJIS['FIRE'])} Branding & Masking", callback_data="manage_branding"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back to Admin", callback_data="admin_panel_back"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def show_manage_force_join(chat_id, message_id):
    settings = get_settings()
    status = f"Active {e('✅', PREMIUM_EMOJIS['DONE'])}" if settings.get("force_join") else f"Disabled {e('❌', PREMIUM_EMOJIS['CLOSE'])}"
    
    text = (f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} <b>FORCE JOIN SYSTEM</b>\n"
            f"━━━━━━━━━━━━━\n\n"
            f"Current Status: <b>{status}</b>\n\n"
            f"<b>Active Channels:</b>\n")
    
    channels = settings.get("channels", [])
    markup = types.InlineKeyboardMarkup()
    
    if not channels:
        text += "  • No channels configured.\n"
    else:
        for i, c in enumerate(channels):
            text += f"  {i+1}. {c['name']} (<code>{c['username']}</code>)\n"
            markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Delete {c['name']}", callback_data=f"del_chan:{i}"))
    
    text += f"\n━━━━━━━━━━━━━"
    
    btn_toggle = f"OFF {e('❌', PREMIUM_EMOJIS['CLOSE'])}" if settings.get("force_join") else f"ON {e('✅', PREMIUM_EMOJIS['DONE'])}"
    markup.row(types.InlineKeyboardButton(f"Toggle Force Join: {btn_toggle}", callback_data="toggle_force_join"))
    markup.row(types.InlineKeyboardButton(f"{e('➕', PREMIUM_EMOJIS['ADD'])} Add Channel", callback_data="add_channel"))
    if channels:
        markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Delete All Channels", callback_data="reset_channels"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def show_manage_admins(chat_id, message_id):
    settings = get_settings()
    text = (f"{e('👤', PREMIUM_EMOJIS['USER'])} <b>ADMIN MANAGEMENT</b>\n"
            f"━━━━━━━━━━━━━\n\n"
            f"Master Admin: <code>{ADMIN_ID}</code> (Immortal)\n\n"
            f"<b>Co-Admins:</b>\n")
    
    admins = settings.get("admins", [])
    markup = types.InlineKeyboardMarkup()
    
    if not admins:
        text += "  • No co-admins added.\n"
    else:
        for a in admins:
            text += f"  • <code>{a}</code>\n"
            markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Remove Admin {a}", callback_data=f"del_admin:{a}"))
            
    text += f"\n━━━━━━━━━━━━━"
    markup.row(types.InlineKeyboardButton(f"{e('➕', PREMIUM_EMOJIS['ADD'])} Add Admin", callback_data="add_admin"))
    if admins:
        markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Remove All Co-Admins", callback_data="reset_admins"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def show_manage_otp_groups(chat_id, message_id):
    settings = get_settings()
    text = (f"{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>OTP GROUP SYSTEM</b>\n"
            f"━━━━━━━━━━━━━\n\n"
            f"<b>Forwarding Groups:</b>\n")
    
    groups = settings.get("otp_groups", [])
    group_buttons = settings.get("group_buttons", {})
    markup = types.InlineKeyboardMarkup()
    
    if not groups:
        text += f"  {e('❌', PREMIUM_EMOJIS['CLOSE'])} No groups added.\n"
    else:
        for g in groups:
            btn_count = len(group_buttons.get(str(g), []))
            text += f"  {e('🔹', PREMIUM_EMOJIS['DOT'])} <code>{g}</code> ({btn_count} Buttons)\n"
            markup.row(types.InlineKeyboardButton(f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} Buttons for {g}", callback_data=f"setup_grp_btns:{g}"),
                       types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Remove", callback_data=f"del_otp_grp:{g}"))
            
    text += (f"\n<b>Global OTP Buttons:</b>\n")
    buttons = settings.get("otp_message_buttons", [])
    if not buttons:
        text += f"  {e('❌', PREMIUM_EMOJIS['CLOSE'])} No global buttons.\n"
    else:
        for i, b in enumerate(buttons):
            text += f"  {i+1}. {b['text']} ({e('🔗', PREMIUM_EMOJIS['PIN'])})\n"
            markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Delete Global: {b['text']}", callback_data=f"del_otp_btn:{i}"))
 
    text += f"\n━━━━━━━━━━━━━"
    markup.row(types.InlineKeyboardButton(f"{e('➕', PREMIUM_EMOJIS['ADD'])} Add Forwarding Group", callback_data="add_otp_group"))
    markup.row(types.InlineKeyboardButton(f"{e('➕', PREMIUM_EMOJIS['ADD'])} Add Global Button", callback_data="add_otp_msg_btn"))
    if groups or buttons:
        markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Reset OTP System", callback_data="reset_otp_groups"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def show_group_buttons_settings(chat_id, message_id, group_id):
    settings = get_settings()
    group_buttons = settings.get("group_buttons", {}).get(str(group_id), [])
    
    text = (f"{e('💬', PREMIUM_EMOJIS['CHAT'])} <b>BUTTONS FOR GROUP:</b> <code>{group_id}</code>\n"
            f"━━━━━━━━━━━━━\n\n"
            f"These buttons only appear when OTP is forwarded to this specific group.\n\n")
    
    markup = types.InlineKeyboardMarkup()
    if not group_buttons:
        text += f"  {e('❌', PREMIUM_EMOJIS['CLOSE'])} No group-specific buttons.\n"
    else:
        for i, btn in enumerate(group_buttons):
            text += f"  {i+1}. {btn['text']} ({e('🔗', PREMIUM_EMOJIS['PIN'])})\n"
            markup.row(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Delete: {btn['text']}", callback_data=f"del_grp_spec_btn:{group_id}:{i}"))
            
    markup.row(types.InlineKeyboardButton(f"{e('➕', PREMIUM_EMOJIS['ADD'])} Add Button", callback_data=f"add_grp_spec_btn:{group_id}"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="manage_otp_groups"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def show_branding_settings(chat_id, message_id):
    brand = get_brand()
    mask = get_mask()
    text = (f"{e('✨', PREMIUM_EMOJIS['FIRE'])} <b>BRANDING & MASKING</b>\n"
            f"━━━━━━━━━━━━━\n\n"
            f"Current Brand Name: <b>{brand}</b>\n"
            f"Current Mask Text: <b>{mask}</b> (Used like 123{mask}4567)\n\n"
            f"━━━━━━━━━━━━━")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f"{e('✏️', PREMIUM_EMOJIS['NOTE'])} Edit Brand Name", callback_data="set_brand_name"))
    markup.row(types.InlineKeyboardButton(f"{e('✏️', PREMIUM_EMOJIS['NOTE'])} Edit Mask Text", callback_data="set_mask_text"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def show_bot_keypad_settings(chat_id, message_id):
    settings = get_settings()
    link = settings.get("otp_link", "https://t.me/dxaotpzone")
    text = (f"{e('🔗', PREMIUM_EMOJIS['PIN'])} <b>BOT OTP BUTTON LINK</b>\n"
            f"━━━━━━━━━━━━━\n\n"
            f"This link is used for the '{e('💬', PREMIUM_EMOJIS['CHAT'])} OTP Group' button displayed after a user allocates numbers.\n\n"
            f"Current Link: <b>{link}</b>\n\n"
            f"━━━━━━━━━━━━━")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f"{e('✏️', PREMIUM_EMOJIS['NOTE'])} Edit Link", callback_data="set_otp_link"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='HTML')

def process_otp_btn_add(msg):
    if msg.text and "|" in msg.text:
        parts = [p.strip() for p in msg.text.split("|")]
        if len(parts) == 2:
            settings = get_settings()
            if "otp_message_buttons" not in settings: settings["otp_message_buttons"] = []
            settings["otp_message_buttons"].append({"text": parts[0], "url": parts[1]})
            write_json("settings.json", settings)
            bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Custom OTP button added!")
    
    time.sleep(1)
    show_manage_otp_groups(msg.chat.id, call_back_msg_id(msg.chat.id))

def process_brand_name_set(msg):
    if msg.text:
        new_brand = msg.text.strip()
        settings = get_settings()
        settings["brand_name"] = new_brand
        write_json("settings.json", settings)
        bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Brand name updated to <b>{new_brand}</b>!")
    
    time.sleep(1)
    show_branding_settings(msg.chat.id, last_menus.get(msg.chat.id))

def process_mask_text_set(msg):
    if msg.text:
        new_mask = msg.text.strip()
        settings = get_settings()
        settings["mask_text"] = new_mask
        write_json("settings.json", settings)
        bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Mask text updated to <b>{new_mask}</b>!")
    
    time.sleep(1)
    show_branding_settings(msg.chat.id, last_menus.get(msg.chat.id))

def process_grp_spec_btn_add(msg, group_id):
    if msg.text and "|" in msg.text:
        parts = [p.strip() for p in msg.text.split("|")]
        if len(parts) == 2:
            settings = get_settings()
            if "group_buttons" not in settings: settings["group_buttons"] = {}
            gid_str = str(group_id)
            if gid_str not in settings["group_buttons"]: settings["group_buttons"][gid_str] = []
            settings["group_buttons"][gid_str].append({"text": parts[0], "url": parts[1]})
            write_json("settings.json", settings)
            bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Button added for group {group_id}!")
    
    time.sleep(1)
    show_group_buttons_settings(msg.chat.id, last_menus.get(msg.chat.id), group_id)

def call_back_msg_id(chat_id):
    return last_menus.get(chat_id)

def process_channel_add(msg):
    if msg.text and "|" in msg.text:
        try:
            parts = [p.strip() for p in msg.text.split("|")]
            if len(parts) == 3:
                name, url, username = parts
                settings = get_settings()
                settings["channels"].append({"name": name, "url": url, "username": username})
                write_json("settings.json", settings)
                bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Channel added successfully!")
        except: pass
    
    time.sleep(1)
    show_manage_force_join(msg.chat.id, last_menus.get(msg.chat.id))

def process_admin_add(msg):
    if msg.text and msg.text.isdigit():
        new_id = msg.text.strip()
        settings = get_settings()
        if new_id not in settings.get("admins", []):
            settings["admins"].append(new_id)
            write_json("settings.json", settings)
            bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Admin ID {new_id} added successfully!")
    
    time.sleep(1)
    show_manage_admins(msg.chat.id, last_menus.get(msg.chat.id))

def process_otp_group_add(msg):
    if msg.text:
        new_id = msg.text.strip()
        settings = get_settings()
        if new_id not in settings.get("otp_groups", []):
            settings["otp_groups"].append(new_id)
            write_json("settings.json", settings)
            bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} OTP Group {new_id} added successfully!")
    
    time.sleep(1)
    show_manage_otp_groups(msg.chat.id, last_menus.get(msg.chat.id))

def process_otp_link_set(msg):
    if msg.text and msg.text.startswith("http"):
        new_url = msg.text.strip()
        settings = get_settings()
        settings["otp_link"] = new_url
        write_json("settings.json", settings)
        bot.send_message(msg.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} OTP Group link updated!")
    
    time.sleep(1)
    show_bot_keypad_settings(msg.chat.id, last_menus.get(msg.chat.id))

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
    markup.row(types.InlineKeyboardButton(f"{e('📤', PREMIUM_EMOJIS['UPLOAD'])} Upload Numbers", callback_data="admin_upload"),
               types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} Delete Files", callback_data="admin_delete_files"))
    markup.row(types.InlineKeyboardButton(f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} Broadcast", callback_data="admin_broadcast"),
               types.InlineKeyboardButton(f"{e('⚙️', PREMIUM_EMOJIS['SETTINGS'])} Settings", callback_data="admin_settings"))
    markup.row(types.InlineKeyboardButton(f"{e('✅', PREMIUM_EMOJIS['DONE'])} Used Numbers", callback_data="view_used"),
               types.InlineKeyboardButton(f"{e('🚀', PREMIUM_EMOJIS['ROCKET'])} Unused Numbers", callback_data="view_unused"))
    markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="close_menu"))

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
    # Set Menu Button
    try: bot.set_chat_menu_button(msg.chat.id, types.MenuButtonCommands())
    except: pass
    
    users = read_json("users.json")
    if not any(u['uid'] == str(user_id) for u in users):
        users.append({'uid': str(user_id), 'username': msg.from_user.username, 'time': str(datetime.now())})
        write_json("users.json", users)

    delete_last_menu(msg.chat.id, user_id)

    if not check_join(user_id):
        show_force_join_msg(msg.chat.id)
        return

    brand = get_brand()
    text = (f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗡𝗨𝗠𝗕𝗘𝗥 𝗕𝗢𝗧 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 》═\n"
            f"━━━━━━━━━━━\n"
            f"{e('👋', PREMIUM_EMOJIS['HELLO'])} 𝗛𝗲𝗹𝗹𝗼, <b>{msg.from_user.first_name}</b>! 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘\n"
            f"{e('💬', PREMIUM_EMOJIS['CHAT'])} 𝗦𝘆𝘀𝘁𝗲𝗺 𝗥𝗲𝗮𝗱𝘆 𝘁𝗼 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲 𝗡𝘂𝗺𝗯𝗲𝗿𝘀\n"
            f"━━━━━━━━━━━\n"
            f"{e('📌', PREMIUM_EMOJIS['PIN'])} 𝗧𝗮𝗽 ➤ 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥\n"
            f"➤ 𝗧𝗼 𝗦𝘁𝗮𝗿𝘁 𝗦𝗲𝗿𝘃𝗶𝗰𝗲\n"
            f"━━━━━━━━━━━\n"
            f"{e('😒', PREMIUM_EMOJIS['DXA'])} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘\n"
            f"━━━━━━━━━━━")
    sent = bot.send_message(msg.chat.id, text, reply_markup=get_main_keyboard(user_id))
    last_menus[user_id] = sent.message_id

@bot.message_handler(commands=['menu'])
def menu_cmd(msg):
    user_id = msg.from_user.id
    brand = get_brand()
    text = (f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗠𝗘𝗡𝗨 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 》═\n"
            f"━━━━━━━━━━━\n"
            f"{e('📱', PREMIUM_EMOJIS['NUMBERS'])} 𝗬𝗼𝘂𝗿 𝗣𝗲𝗿𝘀𝗶𝘀𝘁𝗲𝗻𝘁 𝗠𝗲𝗻𝘂 𝗶𝘀 𝗥𝗲𝗮𝗱𝘆\n"
            f"━━━━━━━━━━━\n"
            f"{e('😒', PREMIUM_EMOJIS['DXA'])} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>{brand}</b>")
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
        text = (f"═《 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 𝗗𝗫𝗔 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 {e('🔥', PREMIUM_EMOJIS['FIRE'])} 》═\n"
                f"━━━━━━━━━━━\n"
                f"{e('👋', PREMIUM_EMOJIS['HELLO'])} 𝗛𝗲𝗹𝗹𝗼, <b>{msg.from_user.first_name}</b>!\n"
                f"{e('💬', PREMIUM_EMOJIS['CHAT'])} 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗫𝗔 𝗦𝘂ｐ𝗽𝗼𝗿𝘁 𝗣𝗮𝗻𝗲𝗹\n"
                f"➤ 𝗧𝗲𝗹𝗹 𝗠𝗲 𝗛𝗼𝘄 𝗖𝗮𝗻 𝗜 𝗛𝗲𝗹𝗽 𝗬𝗼𝘂.\n"
                f"{e('📌', PREMIUM_EMOJIS['PIN'])} 𝗧𝗮ｐ 𝗦𝘂ｐ𝗽𝗼𝗿𝘁 𝗕𝘂𝘁𝘁𝗼𝗻\n"
                f"➤ 𝗧𝗼 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗧𝗵𝗲 𝗔𝗱𝗺𝗶𝗻!\n"
                f"━━━━━━━━━━━\n"
                f"😒 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘</b>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('💬', PREMIUM_EMOJIS['SUPPORT'])} Support Center", url="https://t.me/asik_x_bd_bot"))
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="close_menu"))
        sent = bot.send_message(chat_id, text, reply_markup=markup)
        last_menus[user_id] = sent.message_id
        
    elif (msg.text == "👑 Admin Panel" or msg.text == "👑 Menu Builder") and is_admin(user_id):
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

    if data != "check_join" and not check_join(user_id):
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        show_force_join_msg(chat_id)
        return

    ADMIN_ACTIONS = [
        "manage_force_join", "manage_admins", "manage_otp_groups", "manage_bot_otp_link", 
        "admin_settings", "add_admin", "reset_admins", "add_otp_group", "reset_otp_groups",
        "set_otp_link", "toggle_force_join", "reset_channels", "add_channel", "admin_upload",
        "admin_broadcast", "admin_delete_files", "admin_panel_back", "view_used", "view_unused",
        "add_otp_msg_btn", "manage_branding", "set_brand_name", "set_mask_text", "setup_grp_btns:",
        "add_grp_spec_btn:", "del_grp_spec_btn:"
    ]
    
    is_admin_action = any(data.startswith(act) for act in ADMIN_ACTIONS) or \
                      any(data.startswith(pref) for pref in ["del_chan:", "del_admin:", "del_otp_grp:", "del_otp_btn:", "del_file:", "setup_grp_btns:", "add_grp_spec_btn:", "del_grp_spec_btn:"])
    
    if is_admin_action and not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Limited to Admins only!", show_alert=True)
        return

    if data == "check_join":
        if check_join(user_id):
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            start(call.message)
        else:
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Join all channels first!", show_alert=True)
            
    elif data == "manage_force_join":
        show_manage_force_join(chat_id, call.message.message_id)

    elif data == "manage_admins":
        show_manage_admins(chat_id, call.message.message_id)

    elif data == "manage_otp_groups":
        show_manage_otp_groups(chat_id, call.message.message_id)

    elif data == "manage_bot_otp_link":
        show_bot_keypad_settings(chat_id, call.message.message_id)

    elif data == "manage_branding":
        show_branding_settings(chat_id, call.message.message_id)

    elif data == "set_brand_name":
        text = (f"{e('✏️', PREMIUM_EMOJIS['NOTE'])} <b>EDIT BRAND NAME</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Send the new brand name (e.g., DXA UNIVERSE):")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="manage_branding"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_brand_name_set)

    elif data == "set_mask_text":
        text = (f"{e('✏️', PREMIUM_EMOJIS['NOTE'])} <b>EDIT MASK TEXT</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Send the new mask string (e.g., DXA):")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="manage_branding"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_mask_text_set)

    elif data.startswith("setup_grp_btns:"):
        gid = data.split(":")[1]
        show_group_buttons_settings(chat_id, call.message.message_id, gid)

    elif data.startswith("add_grp_spec_btn:"):
        gid = data.split(":")[1]
        text = (f"{e('➕', PREMIUM_EMOJIS['ADD'])} <b>ADD BUTTON FOR {gid}</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Format: <code>Button Name | https://link.com</code>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data=f"setup_grp_btns:{gid}"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        bot.register_next_step_handler(sent, lambda m: process_grp_spec_btn_add(m, gid))

    elif data.startswith("del_grp_spec_btn:"):
        parts = data.split(":")
        gid, idx = parts[1], int(parts[2])
        settings = get_settings()
        if str(gid) in settings.get("group_buttons", {}):
            btns = settings["group_buttons"][str(gid)]
            if 0 <= idx < len(btns):
                btns.pop(idx)
                write_json("settings.json", settings)
                bot.answer_callback_query(call.id, "Button Removed")
        show_group_buttons_settings(chat_id, call.message.message_id, gid)

    elif data.startswith("del_chan:"):
        idx = int(data.split(":")[1])
        settings = get_settings()
        if 0 <= idx < len(settings["channels"]):
            removed = settings["channels"].pop(idx)
            write_json("settings.json", settings)
            bot.answer_callback_query(call.id, f"Deleted {removed['name']}")
        show_manage_force_join(chat_id, call.message.message_id)

    elif data.startswith("del_admin:"):
        uid = data.split(":")[1]
        settings = get_settings()
        if uid in settings["admins"]:
            settings["admins"].remove(uid)
            write_json("settings.json", settings)
            bot.answer_callback_query(call.id, f"Removed Admin {uid}")
        show_manage_admins(chat_id, call.message.message_id)

    elif data.startswith("del_otp_grp:"):
        gid = data.split(":")[1]
        settings = get_settings()
        if gid in settings["otp_groups"]:
            settings["otp_groups"].remove(gid)
            write_json("settings.json", settings)
            bot.answer_callback_query(call.id, f"Removed Group {gid}")
        show_manage_otp_groups(chat_id, call.message.message_id)

    elif data.startswith("del_otp_btn:"):
        idx = int(data.split(":")[1])
        settings = get_settings()
        if 0 <= idx < len(settings.get("otp_message_buttons", [])):
            settings["otp_message_buttons"].pop(idx)
            write_json("settings.json", settings)
            bot.answer_callback_query(call.id, "Button Deleted")
        show_manage_otp_groups(chat_id, call.message.message_id)

    elif data == "add_otp_msg_btn":
        text = (f"{e('➕', PREMIUM_EMOJIS['ADD'])} <b>ADD OTP BUTTON</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Send button details as:\n"
                f"<code>Button Name | https://link.com</code>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="manage_otp_groups"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        bot.register_next_step_handler(sent, process_otp_btn_add)

    elif data == "admin_settings":
        show_settings_panel(chat_id, call.message.message_id)
        
    elif data == "add_admin":
        text = (f"{e('➕', PREMIUM_EMOJIS['ADD'])} <b>ADD NEW ADMIN</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Please send the Telegram User ID of the new admin:")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_admin_add)

    elif data == "reset_admins":
        settings = get_settings()
        settings["admins"] = []
        write_json("settings.json", settings)
        bot.answer_callback_query(call.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Admins list cleared! (except Master)")
        show_settings_panel(chat_id, call.message.message_id)

    elif data == "add_otp_group":
        text = (f"{e('➕', PREMIUM_EMOJIS['ADD'])} <b>ADD OTP GROUP</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Please send the Group/Channel ID where OTPs should be forwarded:")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_otp_group_add)

    elif data == "reset_otp_groups":
        settings = get_settings()
        settings["otp_groups"] = []
        write_json("settings.json", settings)
        bot.answer_callback_query(call.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} OTP Groups list cleared!")
        show_settings_panel(chat_id, call.message.message_id)

    elif data == "set_otp_link":
        text = (f"{e('🔗', PREMIUM_EMOJIS['PIN'])} <b>SET OTP GROUP LINK</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Please send the invitation URL for your OTP group:")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_otp_link_set)

    elif data == "toggle_force_join":
        settings = get_settings()
        settings["force_join"] = not settings.get("force_join")
        write_json("settings.json", settings)
        bot.answer_callback_query(call.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Settings Updated!")
        show_settings_panel(chat_id, call.message.message_id)

    elif data == "reset_channels":
        settings = get_settings()
        settings["channels"] = []
        write_json("settings.json", settings)
        bot.answer_callback_query(call.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Channels list cleared!")
        show_settings_panel(chat_id, call.message.message_id)

    elif data == "add_channel":
        text = (f"{e('➕', PREMIUM_EMOJIS['ADD'])} <b>ADD NEW CHANNEL</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Please send channel details in following format:\n\n"
                f"<code>Channel Name | Public URL | @Username</code>\n\n"
                f"Example:\n"
                f"<code>My Channel | https://t.me/mychan | @mychan</code>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_settings"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_channel_add)

    elif data == "close_menu":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        
    elif data.startswith("sel_service:"):
        service = data.split(":")[1]
        nums = read_json("numbers.json")
        available = [n for n in nums if not n.get('used') and n.get('service') == service]
        
        if not available:
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Sorry, {service} is currently out of stock!", show_alert=True)
            return

        countries = sorted(list(set([n['country'] for n in available if n.get('country')])))
        
        if not countries:
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} No regions found for this service.", show_alert=True)
            return

        markup = types.InlineKeyboardMarkup()
        for country in countries:
            markup.add(types.InlineKeyboardButton(f"📍 {country}", callback_data=f"sel_country:{service}:{country}"))
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="back_to_services"))
        
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
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Please wait {int(10-diff)} seconds!", show_alert=True)
            return

        parts = data.split(":")
        service, country = parts[1], parts[2]
        all_nums = read_json("numbers.json")
        available = [n for n in all_nums if not n.get('used') and n.get('service') == service and n.get('country') == country]
        
        if len(available) < 3:
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Not enough numbers available.", show_alert=True)
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

        s_key = service.upper().replace(' ', '')
        prem = APP_EMOJIS.get(s_key)
        icon = e(prem[0], prem[1]) if prem else e("🖥", PREMIUM_EMOJIS['SUPPORT'])

        text = (f"━━━━━━━━━━━\n"
                f"《 {e('✅', PREMIUM_EMOJIS['DONE'])} 𝗡𝗨𝗠𝗕𝗘𝗥𝗦 𝗔𝗟𝗟𝗢𝗖𝗔𝗧𝗘𝗗 》\n"
                f"━━━━━━━━━━━\n"
                f"<blockquote>{e('🔹', PREMIUM_EMOJIS['DOT'])} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲</b> {icon} <b>{service}</b></blockquote>\n"
                f"<blockquote>{e('📍', PREMIUM_EMOJIS['PIN'])} <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆</b> 🌐 <b>{country}</b></blockquote>\n"
                f"━━━━━━━━━━━\n"
                f"{chr(10).join(formatted)}\n"
                f"━━━━━━━━━━━\n"
                f"{e('😒', PREMIUM_EMOJIS['DXA'])} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘</b>\n"
                f"━━━━━━━━━━━")
        
        markup = types.InlineKeyboardMarkup()
        otp_btn_link = get_settings().get("otp_link", "https://t.me/dxaotpzone")
        markup.row(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"sel_country:{service}:{country}"))
        markup.row(types.InlineKeyboardButton(f"{e('💬', PREMIUM_EMOJIS['CHAT'])} OTP Group", url=otp_btn_link))
        markup.row(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="back_to_services"))
        
        try: bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        except: pass

    elif data == "admin_upload":
        text = f"{e('📤', PREMIUM_EMOJIS['UPLOAD'])} <b>UPLOAD NUMBERS</b>\n━━━━━━━━━━━━━\nPlease send the .txt file containing numbers."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_panel_back"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, handle_admin_upload_file)

    elif data == "admin_broadcast":
        text = f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} <b>BROADCAST MESSAGE</b>\n━━━━━━━━━━━━━\nSend message to broadcast:"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_panel_back"))
        sent = bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(sent, process_broadcast)

    elif data == "admin_delete_files":
        files = read_json("files.json")
        if not files:
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} No files found.")
            return
        markup = types.InlineKeyboardMarkup()
        for f in files:
            markup.add(types.InlineKeyboardButton(f"{e('🗑', PREMIUM_EMOJIS['DELETE'])} {f['fileName']} ({f['service']})", callback_data=f"del_file:{f['id']}"))
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_panel_back"))
        try: bot.edit_message_text("Select a file to delete:", chat_id, call.message.message_id, reply_markup=markup)
        except: pass

    elif data.startswith("del_file:"):
        fid = data.split(":")[1]
        files = read_json("files.json")
        nums = read_json("numbers.json")
        files = [f for f in files if f['id'] != fid]
        nums = [n for n in nums if n.get('fileId') != fid]
        write_json("files.json", files)
        write_json("numbers.json", nums)
        bot.answer_callback_query(call.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Deleted!")
        show_admin_panel(chat_id, call.message.message_id)

    elif data == "view_used" or data == "view_unused":
        is_used = "used" in data
        all_nums = read_json("numbers.json")
        nums = [n for n in all_nums if bool(n.get('used', False)) == is_used]
        
        service_counts = {}
        for n in nums:
            s_name = n.get('service', 'Other')
            service_counts[s_name] = service_counts.get(s_name, 0) + 1
        
        breakdown_text = ""
        for s in sorted(service_counts.keys()):
            breakdown_text += f"  • {s}: <b>{service_counts[s]}</b>\n"
        
        if not breakdown_text: breakdown_text = "  • No numbers found.\n"

        recent_data = ""
        if nums:
            recent_data = "\n<b>Recent Numbers:</b>\n"
            for n in list(reversed(nums))[:10]:
                recent_data += f"  • <code>{n.get('number')}</code> ({n.get('service')})\n"

        icon = e("✅", PREMIUM_EMOJIS['DONE']) if is_used else e("🚀", PREMIUM_EMOJIS['ROCKET'])
        label = "USED" if is_used else "UNUSED"
        
        text = (f"{icon} <b>{label} NUMBERS</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"Total: <b>{len(nums)}</b>\n\n"
                f"<b>Service Stock:</b>\n"
                f"{breakdown_text}"
                f"{recent_data}\n"
                f"You can download the full list as a .txt file below.\n"
                f"━━━━━━━━━━━━━")
                
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{e('📥', PREMIUM_EMOJIS['FILE'])} Download {label.capitalize()} (.txt)", callback_data=f"download_{label.lower()}"))
        markup.add(types.InlineKeyboardButton(f"{e('🔙', PREMIUM_EMOJIS['CLOSE'])} Back", callback_data="admin_panel_back"))
        try: bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        except: pass

    elif data.startswith("download_"):
        is_used = "used" in data
        nums = [n['number'] for n in read_json("numbers.json") if n.get('used') == is_used]
        if not nums:
            bot.answer_callback_query(call.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Empty list.")
            return
        import io
        buf = io.BytesIO("\n".join(nums).encode())
        buf.name = f"{'used' if is_used else 'unused'}.txt"
        bot.send_document(chat_id, buf)

    elif data == "admin_panel_back":
        bot.clear_step_handler_by_chat_id(chat_id)
        show_admin_panel(chat_id, call.message.message_id)

# --- Admin Operations outside Callback ---
def handle_admin_upload_file(msg):
    if not is_admin(msg.from_user.id): return
    if not msg.document or not msg.document.file_name.endswith('.txt'):
        bot.send_message(msg.chat.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Please send a valid .txt file.")
        return
    
    s_msg = bot.send_message(msg.chat.id, f"{e('🔹', PREMIUM_EMOJIS['DOT'])} Enter Service Name:", parse_mode='HTML')
    bot.register_next_step_handler(s_msg, lambda m: process_service_name(m, msg.document))

def process_service_name(m, doc):
    service_name = m.text
    c_msg = bot.send_message(m.chat.id, f"{e('📍', PREMIUM_EMOJIS['PIN'])} Enter Country Name:", parse_mode='HTML')
    bot.register_next_step_handler(c_msg, lambda m2: process_country_name(m2, doc, service_name))

def process_country_name(m, doc, service_name):
    country_name = m.text
    wait_msg = bot.send_message(m.chat.id, f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} Processing...", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        
        numbers = read_json("numbers.json")
        files = read_json("files.json")
        fid = str(int(time.time()))
        
        files.append({'id': fid, 'fileName': doc.file_name, 'service': service_name, 'country': country_name, 'count': len(lines)})
        
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
        bot.delete_message(m.chat.id, wait_msg.message_id)
        bot.send_message(m.chat.id, f"{e('✅', PREMIUM_EMOJIS['DONE'])} Success! {len(lines)} numbers added.")
    except Exception as ex:
        bot.send_message(m.chat.id, f"{e('❌', PREMIUM_EMOJIS['CLOSE'])} Error: {str(ex)}")

def process_broadcast(msg):
    if msg.text and (msg.text.startswith('/') or msg.text in ["📱 Get Number", "🛠 Support", "👑 Admin Panel", "👑 Menu Builder"]):
        return

    users = read_json("users.json")
    chat_id = msg.chat.id
    
    status_msg = bot.send_message(chat_id, f"{e('📢', PREMIUM_EMOJIS['BROADCAST'])} Broadcasting...", parse_mode='HTML')
    
    count = 0
    for u in users:
        try:
            bot.copy_message(u['uid'], chat_id, msg.message_id)
            count += 1
        except: pass
        
    bot.edit_message_text(f"{e('✅', PREMIUM_EMOJIS['DONE'])} Broadcast complete! Sent to {count} users.", chat_id, status_msg.message_id)

# --- OTP Background Processor ---
def normalize_num(num):
    return re.sub(r'\D', '', str(num))

def get_service_info(original_service, content):
    text = content.upper()
    service = original_service
    
    keywords = [
        {'key': 'INSTAGRAM', 'name': 'Instagram'},
        {'key': 'WHATSAPP', 'name': 'WhatsApp'},
        {'key': 'TELEGRAM', 'name': 'Telegram'},
        {'key': 'FACEBOOK', 'name': 'Facebook'},
        {'key': 'GOOGLE', 'name': 'Google'},
        {'key': 'TIKTOK', 'name': 'TikTok'},
        {'key': 'IMO', 'name': 'Imo'},
        {'key': 'BKASH', 'name': 'bKash'},
        {'key': 'NAGAD', 'name': 'Nagad'}
    ]

    for k in keywords:
        if k['key'] in text:
            service = k['name']
            break

    s_key = service.upper().replace(' ', '')
    prem = APP_EMOJIS.get(s_key)
    icon = e(prem[0], prem[1]) if prem else e("🖥", PREMIUM_EMOJIS['SUPPORT'])
    
    return service, icon

def fetch_otps():
    while True:
        try:
            res = requests.get(f"{OTP_API_URL}?token={OTP_API_TOKEN}&records=50")
            if res.status_code == 200:
                data = res.json()
                settings = get_settings()
                nums_data = read_json("numbers.json")
                for rec in data:
                    if len(rec) < 4: continue
                    serv, full_num, content, tstamp = rec
                    msg_id = f"{full_num}_{tstamp}"
                    if msg_id in processed_messages: continue

                    if len(processed_messages) > 10000:
                        it = iter(processed_messages)
                        next(it)
                        processed_messages.remove(next(it))
                    
                    norm_api = normalize_num(full_num)
                    
                    otp_match = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                    if otp_match:
                        code = otp_match.group(0)
                        serv_key = str(serv).upper().replace(" ", "")
                        
                        premium = APP_EMOJIS.get(serv_key)
                        if premium:
                            icon = e(premium[0], premium[1])
                        else:
                            icon = e("🖥", PREMIUM_EMOJIS['SUPPORT'])
                        
                        # 1. ALWAYS Forward to OTP Groups
                        mask = get_mask()
                        masked_num = f"{norm_api[:3]}{mask}{norm_api[-4:]}" if len(norm_api) >= 7 else norm_api
                        group_body = f"{icon} <b>{serv}</b>  <code>{masked_num}</code>\n\n{e('😒', PREMIUM_EMOJIS['DXA'])} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>{get_brand()}</b>"
                        
                        def get_markup_local(specific_buttons=None):
                            m_obj = {
                                "inline_keyboard": [
                                    [{
                                        "text": f"📋 {code}",
                                        "copy_text": {"text": code}
                                    }]
                                ]
                            }
                            btns = specific_buttons if specific_buttons is not None else settings.get("otp_message_buttons", [])
                            for btn in btns:
                                m_obj["inline_keyboard"].append([{"text": btn["text"], "url": btn["url"]}])
                            return json.dumps(m_obj)

                        group_buttons = settings.get("group_buttons", {})
                        for g_id in settings.get("otp_groups", []):
                            try:
                                target_id = int(g_id) if str(g_id).replace('-', '').isdigit() else g_id
                                spec_btns = group_buttons.get(str(g_id))
                                bot.send_message(target_id, group_body, reply_markup=get_markup_local(spec_btns))
                            except Exception as e_forward:
                                print(f"[OTP] Group {g_id} forward failed: {str(e_forward)}")

                        # 2. Forward to User (Only if assigned & within 24h)
                        match = next((n for n in nums_data if n.get('used') and (normalize_num(n['number']) == norm_api or normalize_num(n['number']).endswith(norm_api) or norm_api.endswith(normalize_num(n['number'])))), None)
                        if match:
                            iso_ts = tstamp.replace(" ", "T") if " " in tstamp else tstamp
                            try:
                                msg_time = datetime.fromisoformat(iso_ts).timestamp() * 1000
                                if msg_time >= (match.get('assignedAt', 0) - 86400000):
                                    body = f"{icon} <b>{serv}</b>  <code>{norm_api}</code>"
                                    bot.send_message(match['assignedTo'], body, reply_markup=get_markup_local())
                            except: pass

                    processed_messages.add(msg_id)
                    continue

                    # Old Match Logic
                    match_old = next((n for n in nums_data if n.get('used') and (normalize_num(n['number']) == norm_api or normalize_num(n['number']).endswith(norm_api) or norm_api.endswith(normalize_num(n['number'])))), None)
                    
                    if match:
                        iso_ts = tstamp.replace(" ", "T") if " " in tstamp else tstamp
                        try:
                            msg_time = datetime.fromisoformat(iso_ts).timestamp() * 1000
                            if msg_time < (match.get('assignedAt', 0) - 10000):
                                processed_messages.add(msg_id)
                                continue
                        except: pass

                        otp_match = re.search(r'\d{3}[- ]\d{3}', content) or re.search(r'\d{4,8}', content)
                        code = otp_match.group(0) if otp_match else str(content)
                        
                        if content:
                            refined_service, service_icon = get_service_info(serv, content)
                            
                            body = f"{service_icon} {refined_service} <code>{norm_api}</code>"
                            mask = get_mask()
                            masked_num = f"{norm_api[:3]}{mask}{norm_api[-4:]}" if len(norm_api) >= 7 else norm_api
                            group_body = f"{service_icon} {refined_service} <code>{masked_num}</code>"

                            def get_markup(specific_buttons=None):
                                m_obj = {
                                    "inline_keyboard": [
                                        [{
                                            "text": f"📋 {code}",
                                            "copy_text": {"text": code}
                                        }]
                                    ]
                                }
                                btns = specific_buttons if specific_buttons is not None else settings.get("otp_message_buttons", [])
                                for btn in btns:
                                    m_obj["inline_keyboard"].append([{"text": btn["text"], "url": btn["url"]}])
                                return json.dumps(m_obj)
                            
                            bot.send_message(match['assignedTo'], body, reply_markup=get_markup())
                            
                            group_buttons = settings.get("group_buttons", {})
                            for g_id in settings.get("otp_groups", []):
                                try:
                                    target_id = g_id
                                    if str(g_id).replace('-', '').isdigit():
                                        target_id = int(g_id)
                                    
                                    # Use group-specific buttons or fallback to global ones
                                    spec_btns = group_buttons.get(str(g_id))
                                    bot.send_message(target_id, group_body, reply_markup=get_markup(spec_btns))
                                except Exception as e_forward:
                                    print(f"[OTP] Forward to {g_id} failed: {str(e_forward)}")
                                
                            processed_messages.add(msg_id)
            time.sleep(5)
        except:
            time.sleep(10)

if __name__ == "__main__":
    # Setup Bot Commands
    try:
        bot.set_my_commands([
            types.BotCommand("start", "Start the bot"),
            types.BotCommand("menu", "Show Main Menu"),
            types.BotCommand("support", "Contact Support")
        ])
    except: pass
    
    threading.Thread(target=fetch_otps, daemon=True).start()
    print("Bot is running...")
    bot.infinity_polling()
