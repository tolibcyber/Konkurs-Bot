import sqlite3
from datetime import datetime

ADMIN_ID = 7288739341 

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # 1. Foydalanuvchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 2. Nomzodlar (Ishtirokchilar) jadvali
    # PRIMARY KEY sifatida (username, chat_id) birikmasini qoldirdik
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        username TEXT, 
        chat_id TEXT,
        votes INTEGER DEFAULT 0,
        post_id INTEGER DEFAULT 0,
        PRIMARY KEY (username, chat_id))''') 
    
    # 3. Ovozlar jadvali (Ovozli batl uchun)
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER, 
        candidate_username TEXT)''')
    
    # 4. Obuna kanallari jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY)''')
    
    # 5. Kommentariyalarni sanash jadvali (Yangi Battle uchun)
    cursor.execute('''CREATE TABLE IF NOT EXISTS commenters (
        post_id INTEGER, 
        user_id INTEGER, 
        UNIQUE(post_id, user_id))''')
    
    # Standart kanalni qo'shish
    cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES ('@TolibTokyo')")
    
    conn.commit()
    conn.close()

# --- FOYDALANUVCHILAR BILAN ISHLASH ---
def add_user(user_id, username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

def get_total_users():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- NOMZODLAR (CANDIDATES) BILAN ISHLASH ---
def add_candidate_to_db(username, chat_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO candidates (username, votes, chat_id) VALUES (?, 0, ?)", 
            (username, str(chat_id))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Baza xatosi: {e}")
        return False
    finally:
        conn.close()

def update_candidate_post_id(username, post_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET post_id = ? WHERE username = ?", (post_id, username))
    conn.commit()
    conn.close()

def get_all_candidates():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- KANALLAR BILAN ISHLASH ---
def add_channel(username):
    if not username.startswith("@"):
        username = "@" + username
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES (?)", (username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_channels():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
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

# --- KOMMENTARIYALAR BILAN ISHLASH (Yangi funksiyalar) ---
def add_commenter(post_id, user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO commenters (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_unique_comments_count(post_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM commenters WHERE post_id = ?", (post_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Bazani ishga tushirish
init_db()
