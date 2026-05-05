from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# 1. ASOSIY REPLI MENYU (HAMMA TUGMALAR JOYYIDA)
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

# 2. BO'LIMLAR UCHUN INLINE TUGMALAR
def section_inline_kb(callback_data=None, url=None):
    buttons = []
    if url:
        buttons.append([InlineKeyboardButton(text="O'yinga kirish 🚀", web_app=WebAppInfo(url=url))])
    if callback_data:
        buttons.append([InlineKeyboardButton(text="Boshlash ⚡️", callback_data=callback_data)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 3. OVOZLI BATL UCHUN TUGMALAR
def voice_battle_kb(bot_username):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Botni kanalga qo'shish", url=f"https://t.me/{bot_username}?startchannel=true&admin=post_messages+edit_messages+delete_messages")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 4. KANALDAGI ASL KONKURS TUGMALARI (TO'G'IRLANDI)
def get_battle_kb(candidates, bot_username):
    buttons = []
    
    # Ishtirokchilar ro'yxati (Ovoz berish linki bilan)
    for cand in candidates:
        vote_link = f"https://t.me/{bot_username}?start=vote_{cand['username']}"
        buttons.append([InlineKeyboardButton(
            text=f"🔹 @{cand['username']} — {cand['votes']} ovoz", 
            url=vote_link
        )])
    
    # MUHIM: Kanaldagi umumiy ro'yxatga qo'shilish uchun 'join_contest' bo'lishi shart!
    buttons.append([InlineKeyboardButton(
        text="🏆 KONKURSGA QO'SHILISH ➕", 
        callback_data="join_contest" 
    )])
    
    # Natijalar
    buttons.append([InlineKeyboardButton(
        text="📊 Natijalar", 
        callback_data="results"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 5. YANGI BATTLE (BETA) UCHUN ALOHIDA TUGMA
def join_new_battle_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]
    ])

# 6. ENIK-BENIK (TIC-TAC-TOE)
def enik_benik_inline_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinni boshlash 🎮", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 7. ADMIN PANEL MENYUSI
def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Reklama", callback_data="send_ads") 
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 8. MAJBURIY OBUNA TUGMASI
def sub_keyboard(channel_url, ref_link):
    clean_url = channel_url.replace("@", "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{clean_url}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check_sub_{ref_link}")]
    ])

# 9. ODDIY ORQAGA QAYTISH
def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])
