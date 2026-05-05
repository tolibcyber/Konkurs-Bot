from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# 1. ASOSIY REPLI MENYU (5 TA BO'LIM VA ADMIN PANEL)
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
    
    # Admin bo'lsa, panel tugmasini qo'shish
    if str(user_id) == str(admin_id):
        kb.append([KeyboardButton(text="⚙️ Admin Panel")])
        
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang..."
    )

# 2. BARABAN VA BOSHQALAR UCHUN UMUMIY INLINE
def section_inline_kb(url=None, callback_data=None):
    buttons = []
    if url:
        buttons.append([InlineKeyboardButton(text="O'yinga kirish 🚀", web_app=WebAppInfo(url=url))])
    if callback_data:
        buttons.append([InlineKeyboardButton(text="Boshlash ⚡️", callback_data=callback_data)])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 3. OVOZLI BATL UCHUN (BOTNI KANALGA QO'SHISH)
def voice_battle_kb(bot_username):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Botni kanalga qo'shish", 
            url=f"https://t.me/{bot_username}?startchannel=true&admin=post_messages+edit_messages+delete_messages"
        )],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 4. KANALDAGI ASL KONKURS TUGMALARI (RASMDAGI VARIANT)
def get_battle_kb(candidates, bot_username):
    buttons = []
    
    # Ishtirokchilar ro'yxati (Deep-link orqali ovoz berish)
    for cand in candidates:
        # Usernameni @ siz yuborish kerak linkda
        clean_username = cand['username'].replace("@", "")
        vote_link = f"https://t.me/{bot_username}?start=vote_{clean_username}"
        
        buttons.append([InlineKeyboardButton(
            text=f"🔹 @{clean_username} — {cand['votes']} ovoz", 
            url=vote_link
        )])
    
    # Konkursga qo'shilish tugmasi (Callback orqali ishlaydi)
    buttons.append([InlineKeyboardButton(
        text="🏆 KONKURSGA QO'SHILISH ➕", 
        callback_data="join_contest" 
    )])
    
    # Natijalarni ko'rish
    buttons.append([InlineKeyboardButton(
        text="📊 Natijalar", 
        callback_data="results"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 5. ENIK-BENIK (TIC-TAC-TOE)
def enik_benik_inline_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinni boshlash 🎮", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 6. ADMIN PANEL MENYUSI
def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Reklama", callback_data="send_ads") 
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 7. MAJBURIY OBUNA
def sub_keyboard(channel_url, ref_link="none"):
    # URL ni tozalash
    clean_url = channel_url.replace("@", "").replace("https://t.me/", "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{clean_url}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check_sub_{ref_link}")]
    ])

# 8. ODDIY ORQAGA QAYTISH
def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])
