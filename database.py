import sqlite3

# ADMIN_ID ni bu yerga o'z IDingni yoz
ADMIN_ID = 7288739341 

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Nomzodlar jadvali - YANGILANDI: post_id ustuni qo'shildi
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        username TEXT PRIMARY KEY, 
        votes INTEGER DEFAULT 0,
        post_id INTEGER DEFAULT 0)''') # Yangi battle xabarini tahrirlash uchun
    
    # Ovozlar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER, 
        candidate_username TEXT, 
        PRIMARY KEY (user_id, candidate_username))''')
    
    # Sozlamalar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, 
        value TEXT)''')
    
    # @TolibTokyo ni standart kanal sifatida kiritamiz
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel', '@TolibTokyo')")
    
    # Agar jadval avvaldan bo'lsa-yu, post_id bo'lmasa - uni qo'shib qo'yamiz
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN post_id INTEGER DEFAULT 0")
    except:
        pass
    
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# --- YANGI BATTLE UCHUN KERAKLI FUNKSIYALAR ---

def add_candidate_to_db(username):
    """Yangi ishtirokchini bazaga qo'shish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username, votes) VALUES (?, 0)", (username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_candidates():
    """Hamma ishtirokchilarni lug'at ko'rinishida olish (auto-update uchun)"""
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row # Ustun nomlari bilan olish uchun
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- ESKI FUNKSIYALARING (O'ZGARMADI) ---

def get_setting(key):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "@TolibTokyo"

def set_setting(key, value):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_at >= date('now', '-30 days')")
    monthly = cursor.fetchone()[0]
    conn.close()
    return total, monthly

def get_candidates():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes FROM candidates") 
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def get_top_5():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes FROM candidates ORDER BY votes DESC LIMIT 5") 
    res = cursor.fetchall()
    conn.close()
    return res

def get_total_users():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users") 
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_channel(username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
    try:
        cursor.execute("INSERT INTO channels (username) VALUES (?)", (username,))
        conn.commit()
    except: pass
    conn.close()

def get_channels():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
    cursor.execute("SELECT username FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def remove_channel(username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# Bazani ishga tushirish
init_db()
