import sqlite3
from datetime import datetime

# ADMIN_ID o'z joyida
ADMIN_ID = 7288739341 

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Nomzodlar jadvali (chat_id va post_id bilan)
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        username TEXT PRIMARY KEY, 
        votes INTEGER DEFAULT 0,
        post_id INTEGER DEFAULT 0,
        chat_id TEXT DEFAULT NULL)''') 
    
    # Ovozlar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER, 
        candidate_username TEXT, 
        PRIMARY KEY (user_id, candidate_username))''')
    
    # Sozlamalar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, 
        value TEXT)''')
    
    # Majburiy obuna kanallari uchun alohida jadval
    cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY)''')
    
    # Standart kanalni sozlamalarga qo'shish
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel', '@TolibTokyo')")
    
    # Eskidan qolgan bazalarda ustunlar bo'lmasa, qo'shib qo'yamiz
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN post_id INTEGER DEFAULT 0")
    except: pass
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN chat_id TEXT DEFAULT NULL")
    except: pass
    
    conn.commit()
    conn.close()

# --- HANDLERS BILAN ISHLAYDIGAN ASOSIY FUNKSIYALAR ---

def add_candidate_to_db(username, chat_id=None):
    """Ham eski konkurs, ham yangi battle uchun universal funksiya"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        # Agar chat_id bo'lsa yangi battle, bo'lmasa eski uslub
        cursor.execute(
            "INSERT INTO candidates (username, votes, chat_id) VALUES (?, 0, ?)", 
            (username, chat_id)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def update_candidate_post_id(username, post_id):
    """Yangi battledagi ishtirokchi postini yangilash uchun"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET post_id = ? WHERE username = ?", (post_id, username))
    conn.commit()
    conn.close()

def get_all_candidates():
    """Barcha nomzodlarni reyting bo'yicha olish"""
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Ovozlar soniga ko'ra tartiblaymiz
    cursor.execute("SELECT * FROM candidates ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_user(user_id, username):
    """Yangi foydalanuvchini bazaga qo'shish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# --- ADMIN VA SOZLAMALAR FUNKSIYALARI ---

def get_all_user_ids():
    """Rassilka (reklama) uchun barcha IDlarni olish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_total_users():
    """Statistika uchun foydalanuvchilar soni"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users") 
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_channel(username):
    """Majburiy obuna kanalini qo'shish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES (?)", (username,))
        conn.commit()
    except: pass
    finally:
        conn.close()

def get_channels():
    """Barcha majburiy obuna kanallarini olish"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def remove_channel(username):
    """Kanalni majburiy obunadan o'chirish"""
    conn = sqlite3.connect('bot_id.db') # Bu yerda db nomi adashgan bo'lsa bot_data.db qiling
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# Bazani birinchi marta ishga tushirish
init_db()
