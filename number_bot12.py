# --- Part 13: Admin - Broadcast Engine ---
def run_broadcast(msg, chat_id):
    """Reliable broadcast system with progress updates"""
    users = read_json("users.json")
    total = len(users)
    
    status_msg = bot.send_message(chat_id, f"🚀 <b>Starting Broadcast...</b>\nTarget: {total} users")
    
    success = 0
    fail = 0
    
    for idx, user in enumerate(users):
        try:
            bot.copy_message(user['uid'], chat_id, msg.message_id)
            success += 1
        except:
            fail += 1
            
        # Update UI every 20 users
        if (idx + 1) % 20 == 0:
            bot.edit_message_text(
                f"🚀 <b>Broadcasting...</b>\n"
                f"Progress: {idx+1}/{total}\n"
                f"✅ Success: {success}\n"
                f"❌ Failed: {fail}",
                chat_id, status_msg.message_id
            )
            
    bot.send_message(
        chat_id,
        f"✅ <b>Broadcast Finished!</b>\n"
        f"━━━━━━━━━━━━\n"
        f"Total: {total}\n"
        f"Success: {success}\n"
        f"Failed: {fail}"
    )
