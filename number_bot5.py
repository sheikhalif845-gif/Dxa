# --- Part 6: Keyboard & Navigation UI ---
def get_main_keyboard(user_id):
    """Returns the primary navigation keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📱 Get Number", "🛠 Support")
    if is_admin(user_id):
        markup.row("👑 Admin Panel")
    return markup

last_menus = {}  # Track message IDs per user for cleanup

def cleanup_last_menu(user_id, chat_id):
    """Deletes previous inline menus to prevent clutter"""
    if user_id in last_menus:
        try: bot.delete_message(chat_id, last_menus[user_id])
        except: pass
        del last_menus[user_id]
