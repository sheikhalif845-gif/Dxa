# --- Part 12: Admin - File Processing & Stock Upload ---
def handle_file_upload(msg):
    """Processes uploaded .txt files and extracts number data"""
    if not msg.document:
        return bot.send_message(msg.chat.id, "❌ Please upload a .txt file.")
    
    status_msg = bot.send_message(msg.chat.id, f"{e('⏳', PREMIUM_EMOJIS['WAIT'])} Analyzing your file...")
    
    try:
        file_info = bot.get_file(msg.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        
        lines = [L.strip() for L in content.splitlines() if L.strip() and "|" in L]
        if not lines:
            return bot.edit_message_text("❌ No valid lines found! (Format: Number|Service|Country)", msg.chat.id, status_msg.message_id)
            
        numbers_db = read_json("numbers.json")
        files_db = read_json("files.json")
        
        file_id = f"F{int(time.time())}"
        added = 0
        
        for line in lines:
            parts = line.split("|")
            if len(parts) == 3:
                num, srv, cnt = parts
                numbers_db.append({
                    "id": f"{file_id}_{added}",
                    "number": num,
                    "service": srv,
                    "country": cnt,
                    "used": False,
                    "fileId": file_id,
                    "createdAt": str(datetime.now())
                })
                added += 1
                
        files_db.append({
            "id": file_id,
            "name": msg.document.file_name,
            "count": added,
            "date": str(datetime.now())
        })
        
        write_json("numbers.json", numbers_db)
        write_json("files.json", files_db)
        
        bot.edit_message_text(f"✅ <b>Import Successful!</b>\nAdded <b>{added}</b> numbers from <b>{msg.document.file_name}</b>.", msg.chat.id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Processing failed: {str(e)}", msg.chat.id, status_msg.message_id)
