import sqlite3
from datetime import datetime
import logging

ADMIN_ID = 7288739341 

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # 1. Foydalanuvchilar
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 2. Nomzodlar (chat_id va post_id qo'shilgan)
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        username TEXT, 
        chat_id TEXT,
        votes INTEGER DEFAULT 0,
        post_id INTEGER DEFAULT 0,
        PRIMARY KEY (username, chat_id))''') 
    
    # 3. Ovozlar
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER PRIMARY KEY, 
        candidate_username TEXT)''')
    
    # 4. Kanallar
    cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY)''')
    
    # Standart kanalni qo'shish
    cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES ('@TolibTokyo')")
    
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def add_candidate_to_db(username, chat_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        # Avval bu ishtirokchi bazada bor-yo'qligini tekshiramiz
        cursor.execute("SELECT username FROM candidates WHERE username = ?", (username,))
        if cursor.fetchone():
            return False  # Allaqachon bor bo'lsa False qaytaramiz

        # Agar yo'q bo'lsa, qo'shamiz
        cursor.execute("INSERT INTO candidates (username, votes, chat_id) VALUES (?, ?, ?)", (username, 0, chat_id))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Baza xatosi: {e}")
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

init_db()
def add_channel(username):
    """Obuna kanalini bazaga qo'shish"""
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
    """Barcha kanallarni olish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def remove_channel(username):
    """Kanalni o'chirish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Ishtirokchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates 
                      (username TEXT PRIMARY KEY, votes INTEGER DEFAULT 0, 
                       chat_id TEXT, post_id INTEGER)''')
    # Ovozlar jadvali (Ovozli batl uchun)
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes 
                      (user_id INTEGER, candidate_username TEXT)''')
    # KOMMENTLARNI SANASH JADVALI (Yangi)
    cursor.execute('''CREATE TABLE IF NOT EXISTS commenters 
                      (post_id INTEGER, user_id INTEGER, UNIQUE(post_id, user_id))''')
    conn.commit()
    conn.close()

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
