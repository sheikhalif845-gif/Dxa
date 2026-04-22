# --- Part 1: Foundations, Imports and Core Config ---
import telebot
import requests
import json
import os
import time
import threading
import random
import re
import io
from telebot import types
from datetime import datetime

# ==========================================
# ⚙️ GLOBAL CONFIGURATION
# ==========================================
BOT_TOKEN = "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg"
ADMIN_ID = 8197284774
OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats"
OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ=="

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ==========================================
# 🛠️ DATABASE ENGINE (FILE-BASED)
# ==========================================
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def read_json(filename):
    """Mirroring the readJson function from server.ts"""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path): return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def write_json(filename, data):
    """Mirroring the writeJson function from server.ts"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_settings():
    """Exact replica of the settings management logic in server.ts"""
    settings = read_json("settings.json")
    if not settings or isinstance(settings, list):
        default_settings = {
            "force_join": True,
            "channels": [
                {"name": "DXA Universe", "url": "https://t.me/dxa_universe", "username": "@dxa_universe"}
            ],
            "admins": [],
            "otp_groups": [],
            "otp_link": "https://t.me/dxaotpzone",
            "brand_name": "DXA UNIVERSE",
            "mask_text": "DXA",
            "group_buttons": {},
            "otp_message_buttons": []
        }
        write_json("settings.json", default_settings)
        return default_settings
    return settings
