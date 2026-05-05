import sqlite3
import asyncio
import logging
from datetime import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import *

# database.py dan importlar
from database import (
    add_user, ADMIN_ID, get_total_users, 
    get_all_user_ids, add_channel, remove_channel, get_channels
)

router = Router()
REQUIRED_CHANNEL = "@TolibTokyo"
# Bu o'zgaruvchi vaqtinchalik xabar ID sini ushlab turish uchun kerak
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}

class AdminStates(StatesGroup):
    waiting_for_ad = State()
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

# --- 1. BAZA FUNKSIYALARI ---
def add_candidate_to_db(username, chat_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username, votes, chat_id) VALUES (?, ?, ?)", (username, 0, chat_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_candidates():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes, post_id, chat_id FROM candidates ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_candidate_post_id(username, post_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET post_id = ? WHERE username = ?", (post_id, username))
    conn.commit()
    conn.close()

# --- 2. TEKSHIRUV FUNKSIYASI ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- 3. START VA OVOZ BERISH ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username) 

    if not await is_subscribed(message.bot, user_id):
        args = command.args or "none"
        sub_text = (
            f"👋 <b>Assalomu alaykum!</b>\n\n"
            f"Botimizdan foydalanish va konkurslarda qatnashish uchun "
            f"kanalimizga obuna bo'lishingiz shart.\n\n"
            f"📢 <b>Kanal:</b> {REQUIRED_CHANNEL}\n\n"
            f"<i>Obuna bo'lgach, '✅ Tekshirish' tugmasini bosing.</i>"
        )
        return await message.answer(sub_text, reply_markup=sub_keyboard(REQUIRED_CHANNEL, args), parse_mode="HTML")

    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM votes WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return await message.answer("🚫 <b>Kechirasiz!</b>\n\nSiz ushbu konkursda allaqachon bitta nomzodga ovoz berib bo'lgansiz!", parse_mode="HTML")

        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE username = ?", (candidate,))
        conn.commit(); conn.close()
        
        await message.answer(f"✅ Tabriklaymiz! \n\n@{candidate} uchun ovozingiz muvaffaqiyatli qabul qilindi!")
        return

    start_txt = (
        f"👋 Salom {message.from_user.first_name} \n\n"
        f"Sizni botimizda ko'rib turganimizdan xursandmiz! Bu yerda siz quyidagi imkoniyatlarga egasiz:\n\n"
        f"🎡 <b>Baraban:</b> Barabanga Ism Yozib G'olib Aniqlaysiz! Juda zo'r!\n"
        f"✌️ <b>Enik-Benik:</b> Do'stlar bilan qiziqarli o'yinlar o'ynang!\n"
        f"🎤 <b>Ovozli Batl:</b> O'z kanalingizda professional konkurslar tashkil qiling!\n\n"
        f"🚀 <b>Pastdagi menyudan o'zingizga kerakli bo'limni tanlang:</b>"
    )
    await message.answer(start_txt, reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 4. O'YINLAR ---
@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_reply_btn(message: types.Message):
    await message.answer(
        "🎡 <b>Baraban o'yini</b> bo'limini tanladingiz.\n\nOmadingizni sinab ko'rish uchun pastdagi tugmani bosing:",
        reply_markup=section_inline_kb(url="https://barabandev.netlify.app/"),
        parse_mode="HTML"
    )

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_reply_btn(message: types.Message):
    await message.answer(
        "<b>✌️ Enik-Benik o'yiniga xush kelibsiz!</b>\n\n"
        "Bu yerda siz mantiqiy o'yinlar o'ynashingiz mumkin. "
        "Hozircha bizda <b>Tic-Tac-Toe (X-O)</b> o'yini mavjud. 🚀\n\n"
        "O'ynash uchun pastdagi tugmani bosing:",
        reply_markup=enik_benik_inline_kb(url="https://tictac-by-tolib.netlify.app/"),
        parse_mode="HTML"
    )

@router.message(F.text == "🎤 Ovozli Batl")
async def voice_battle_reply_btn(message: types.Message):
    bot_info = await message.bot.get_me()
    guide_text = (
        f"🎤 <b>Ovozli Batl (Konkurs) tashkil qilish bo'yicha to'liq qo'llanma:</b>\n\n"
        f"1️⃣ <b>Botni kanalga qo'shish:</b> Botni o'z kanalingizga admin qiling.\n\n"
        f"2️⃣ <b>Konkursni boshlash:</b> Bot admin bo'lgan kanalingizga <code>#konkursx</code> yoki ushbu bo'limdagi <b>🚀 Yangi Battle</b> tugmasini ishlating.\n\n"
        f"3️⃣ <b>Muhim:</b> Har bir ovoz beruvchi sening kanalingga obuna bo'lishi shart!"
    )
    await message.answer(guide_text, reply_markup=voice_battle_kb(bot_info.username), parse_mode="HTML")

# --- 5. YANGI BATTLE TIZIMI ---
@router.message(F.text == "🚀 Yangi Battle (Beta)")
async def create_new_battle(message: types.Message, state: FSMContext):
    await message.answer("📝 Battle uchun asosiy matnni kiriting (Bu matn siz ko'rsatgan kanalda chiqadi):")
    await state.set_state(AdminStates.waiting_for_battle_text)

@router.message(AdminStates.waiting_for_battle_text)
async def process_b_text(message: types.Message, state: FSMContext):
    await state.update_data(b_text=message.text)
    await message.answer("🆔 Kanal ID yoki @username kiriting (Masalan: @TolibTokyo):")
    await state.set_state(AdminStates.waiting_for_battle_channel)

@router.message(AdminStates.waiting_for_battle_channel)
async def finalize_battle(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel = message.text
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]])
    
    try:
        sent_msg = await message.bot.send_message(chat_id=channel, text=data['b_text'], reply_markup=kb, parse_mode="HTML")
        # Global o'zgaruvchiga saqlaymiz, shunda keyingi ishtirokchilar "reply" qila oladi
        LAST_BATTLE_POST["chat_id"] = sent_msg.chat.id
        LAST_BATTLE_POST["message_id"] = sent_msg.message_id
        await message.answer(f"✅ Battle kanalga muvaffaqiyatli yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: Bot ushbu kanalda admin emas yoki kanal nomi noto'g'ri.")
    await state.clear()

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        return await callback.answer("Konkursda qatnashish uchun kanalga obuna bo'ling!", show_alert=True)

    username = callback.from_user.username or callback.from_user.first_name
    
    # Ishtirokchi posti (Aynan o'sha asosiy postga REPLY qilib yuboradi)
    participant_text = (
        f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{username}\n\n"
        f"❤️ Reaksiyalar: 0/100\n"
        f"💬 Komentlar: 0/100\n"
        f"⭐ Stars: 0\n\n"
        f"📈 <b>UMUMIY BALL: 0</b>"
    )

    try:
        new_post = await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=participant_text,
            reply_to_message_id=callback.message.message_id, # REPLY qilish joyi
            parse_mode="HTML"
        )
        
        if add_candidate_to_db(username, callback.message.chat.id):
            update_candidate_post_id(username, new_post.message_id)
            await callback.answer("Muvaffaqiyatli qo'shildingiz!", show_alert=True)
        else:
            await callback.answer("Siz allaqachon ro'yxatdasiz!", show_alert=True)
    except Exception as e:
        await callback.answer("Xatolik! Bot admin ekanligini tekshiring.", show_alert=True)



# --- ADMIN PANEL ---
@router.message(F.text == "⚙️ Admin Panel")
async def admin_reply_btn(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    await message.answer(
        "<b>⚙️ Admin Paneliga xush kelibsiz!</b>\n\nBu yerdan bot statistikasini ko'rishingiz mumkin.",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("refresh_"))
async def refresh_score(callback: types.CallbackQuery):
    candidate_username = callback.data.replace("refresh_", "")
    
    # Bazadan oxirgi ballarni olamiz
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT votes FROM candidates WHERE username = ?", (candidate_username,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        votes = res[0]
        updated_text = (
            f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{candidate_username}\n\n"
            f"❤️ Reaksiyalar: 0/100\n"
            f"💬 Komentlar: 0/100\n"
            f"⭐ Stars: 0\n\n"
            f"📈 <b>UMUMIY BALL: {votes}</b>\n"
            f"──────────────────\n"
            f"🕒 Oxirgi yangilanish: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        try:
            await callback.message.edit_text(text=updated_text, reply_markup=callback.message.reply_markup, parse_mode="HTML")
            await callback.answer("Ballar yangilandi! ✅")
        except:
            await callback.answer("Ballar hali o'zgarmagan. ⏳")
    else:
        await callback.answer("Ma'lumot topilmadi. ❌")
