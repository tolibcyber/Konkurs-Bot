from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# 1. ASOSIY REPLI MENYU (Barcha bo'limlar ajratilgan)
def main_reply_menu(user_id, admin_id):
    kb = [
        [
            KeyboardButton(text="🎡 Baraban o'yini"),
            KeyboardButton(text="✌️ Enik-Benik")
        ],
        [
            KeyboardButton(text="🎤 Ovozli Batl"),
            KeyboardButton(text="🚀 Yangi Battle (Beta)")
        ]
    ]
    
    if str(user_id) == str(admin_id):
        kb.append([KeyboardButton(text="⚙️ Admin Panel")])
        
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang..."
    )

# 2. OVOZLI BATL UCHUN (Deep-link ovoz berish tizimi)
def get_battle_kb(candidates, bot_username):
    buttons = []
    for cand in candidates:
        clean_username = cand['username'].replace("@", "")
        vote_link = f"https://t.me/{bot_username}?start=vote_{clean_username}"
        
        buttons.append([InlineKeyboardButton(
            text=f"🔹 @{clean_username} — {cand['votes']} ovoz", 
            url=vote_link
        )])
    
    buttons.append([InlineKeyboardButton(text="🏆 KONKURSGA QO'SHILISH ➕", callback_data="join_contest")])
    buttons.append([InlineKeyboardButton(text="📊 Natijalar", callback_data="results")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 3. YANGI BATTLE (BETA) UCHUN - Faqat bitta qatnashish tugmasi
def join_new_battle_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]
    ])

# 4. ADMIN PANEL MENYUSI
def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Reklama", callback_data="send_ads") 
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 5. O'YINLAR UCHUN INLINE (Web App)
def section_inline_kb(url=None, callback_data=None):
    buttons = []
    if url:
        buttons.append([InlineKeyboardButton(text="O'yinga kirish 🚀", web_app=WebAppInfo(url=url))])
    if callback_data:
        buttons.append([InlineKeyboardButton(text="Boshlash ⚡️", callback_data=callback_data)])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 6. MAJBURIY OBUNA
def sub_keyboard(channel_url, ref_link="none"):
    clean_url = channel_url.replace("@", "").replace("https://t.me/", "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{clean_url}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check_sub_{ref_link}")]
    ])

# 7. BOTNI KANALGA QO'SHISH (Admin uchun qulaylik)
def voice_battle_kb(bot_username):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Botni kanalga qo'shish", 
            url=f"https://t.me/{bot_username}?startchannel=true&admin=post_messages+edit_messages+delete_messages"
        )],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])
# keyboard.py faylining eng oxiriga qo'shib qo'y:

# 8. ENIK-BENIK (TIC-TAC-TOE) UCHUN ALOHIDA TUGMA
def enik_benik_inline_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinni boshlash 🎮", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 9. ODDIY ORQAGA QAYTISH TUGMASI
def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])
