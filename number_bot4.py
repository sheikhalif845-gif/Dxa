# --- Part 5: Permissions & Join Check ---
def is_admin(user_id):
    """Mirroring isAdmin from server.ts"""
    if str(user_id) == str(ADMIN_ID): return True
    s = get_settings()
    return str(user_id) in [str(a) for a in s.get("admins", [])]

def check_force_join(user_id):
    """Mirroring checkForceJoin from server.ts"""
    settings = get_settings()
    if not settings.get("force_join") or is_admin(user_id): return True
    
    for channel in settings.get("channels", []):
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                return False
        except Exception as e:
            print(f"Join check failed for {channel['username']}: {e}")
            return False
    return True
