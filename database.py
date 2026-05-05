import sqlite3

# ADMIN_ID ni o'z IDingga almashtir
ADMIN_ID = 7288739341 

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Nomzodlar jadvali - post_id va chat_id BILAN
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        username TEXT PRIMARY KEY, 
        votes INTEGER DEFAULT 0,
        post_id INTEGER DEFAULT 0,
        chat_id INTEGER DEFAULT 0)''') 
    
    # Ovozlar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER, 
        candidate_username TEXT, 
        PRIMARY KEY (user_id, candidate_username))''')
    
    # Sozlamalar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, 
        value TEXT)''')
    
    # Standart kanal
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel', '@TolibTokyo')")
    
    # Agar jadval bo'lsa-yu, ustunlar yo'q bo'lsa - qo'shib qo'yamiz
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN post_id INTEGER DEFAULT 0")
    except: pass
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN chat_id INTEGER DEFAULT 0")
    except: pass
    
    conn.commit()
    conn.close()

# --- YANGI BATTLE FUNKSIYALARI ---

def add_candidate_to_db(username, chat_id):
    """Ishtirokchini chat_id bilan bazaga qo'shish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        # chat_id ni saqlash shart!
        cursor.execute("INSERT INTO candidates (username, votes, chat_id) VALUES (?, 0, ?)", (username, chat_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def update_candidate_post_id(username, post_id):
    """Xabar ID sini saqlash (Yangilash tugmasi ishlashi uchun)"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET post_id = ? WHERE username = ?", (post_id, username))
    conn.commit()
    conn.close()

def get_candidate_votes(username):
    """Faqat bitta nomzodning ovozini olish (Refresh tugmasi uchun)"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT votes FROM candidates WHERE username = ?", (username,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

# --- QOLGAN STANDART FUNKSIYALAR ---

def add_user(user_id, username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users") 
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_channels():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
    cursor.execute("SELECT username FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# Bazani ishga tushirish
init_db()
