from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from database import ADMIN_ID

# 1. ASOSIY REPLI MENYU
def main_reply_menu(user_id, admin_id):
    kb = [
        [
            KeyboardButton(text="🎡 Baraban o'yini"),
            KeyboardButton(text="✌️ Enik-Benik")
        ],
        [
            KeyboardButton(text="🎤 Ovozli Batl")
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

def get_battle_kb(candidates, bot_username):
    buttons = []
    
    # Ko'k rangli fon effekti uchun (🔹 yoki 🔵)
    for cand in candidates:
        vote_link = f"https://t.me/{bot_username}?start=vote_{cand['username']}"
        buttons.append([InlineKeyboardButton(
            text=f"🔹 @{cand['username']} — {cand['votes']} ovoz", 
            url=vote_link
        )])
    
    # Yashil rangli fon effekti (🏆 va ➕ bilan)
    buttons.append([InlineKeyboardButton(
        text="🏆 KONKURSGA QO'SHILISH ➕", 
        callback_data="join_contest"
    )])
    
    # Natijalar (📊 bilan)
    buttons.append([InlineKeyboardButton(
        text="📊 Natijalar", 
        callback_data="results"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Enik-Benik (Tic-Tac-Toe) uchun maxsus tugma
def enik_benik_inline_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'yinni boshlash 🎮", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 5. ADMIN PANEL MENYUSI (TUZATILDI)
def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            # Bu yerda "admin_broadcast" edi, bot kodi bilan moslash uchun "send_ads" qilindi
            InlineKeyboardButton(text="📢 Reklama", callback_data="send_ads") 
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])

# 6. MAJBURIY OBUNA TUGMASI
def sub_keyboard(channel_url, ref_link):
    clean_url = channel_url.replace("@", "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{clean_url}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check_sub_{ref_link}")]
    ])

# 8. ODDIY INLINE ORQAGA QAYTISH
def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
    ])