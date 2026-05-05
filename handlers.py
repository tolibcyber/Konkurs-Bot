import sqlite3
import asyncio
import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# O'zingning fayllaringdan importlar
from keyboard import (
    get_battle_kb, main_reply_menu, voice_battle_kb, 
    section_inline_kb, enik_benik_inline_kb, admin_menu_kb
)
from database import add_user, ADMIN_ID, add_candidate_to_db, update_candidate_post_id

router = Router()

# Konkurs postini xotirada saqlash (Real vaqtda yangilash uchun)
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}

class AdminStates(StatesGroup):
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

def get_all_candidates():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes FROM candidates WHERE chat_id IS NULL OR chat_id = 0 ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- 1. /START XABARI (TO'LIQ VA 5 TA BO'LIM BILAN) ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    # Foydalanuvchini bazaga qo'shish
    add_user(user_id, message.from_user.username) 

    # Ovoz berish qismi (Deep-link)
    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Ovoz berganlikni tekshirish
        cursor.execute("SELECT * FROM votes WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return await message.answer("🚫 <b>Siz allaqachon ovoz bergansiz!</b>\nBitta foydalanuvchi faqat bir marta ovoz bera oladi.")

        # Ovozni hisobga olish
        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE username = ?", (candidate,))
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ <b>@{candidate} uchun ovozingiz qabul qilindi!</b>\nOmad tilaymiz!")
        
        # Kanaldagi postni darhol yangilash
        if LAST_BATTLE_POST["message_id"]:
            bot_info = await message.bot.get_me()
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=LAST_BATTLE_POST["chat_id"],
                    message_id=LAST_BATTLE_POST["message_id"],
                    reply_markup=get_battle_kb(get_all_candidates(), bot_info.username)
                )
            except: pass
        return

    # Asosiy Start matni
    start_text = (
        f"👋 <b>Salom, {message.from_user.first_name}!</b>\n\n"
        "O'yinlar va batllar botiga xush kelibsiz. Bu yerda siz baraban o'ynashingiz, "
        "do'stlaringiz bilan batllarda qatnashishingiz va sovg'alar yutib olishingiz mumkin.\n\n"
        "👇 <b>Davom etish uchun menyudan bo'limni tanlang:</b>"
    )
    await message.answer(start_text, reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 2. KLASSIK OVOZLI BATL (#konkursx) ---
@router.channel_post(F.text.contains("#konkursx"))
@router.message(F.text.contains("#konkursx"))
async def start_contest_handler(message: types.Message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE chat_id IS NULL OR chat_id = 0")
    cursor.execute("DELETE FROM votes")
    conn.commit(); conn.close()

    battle_text = (
        f"<b>{message.chat.title}</b> 🧸\n"
        "🏆 <b>BATL Boshlandi</b>🥳\n\n"
        "<blockquote>❗ Konkurs shartlari shu kanalga obuna bo'lish va "
        "do'stlaringiz sizga ovoz berishini so'rashdan iborat.</blockquote>\n"
        "<blockquote>Agar kanalga qo'shilib ovoz berib chiqib ketsa ovozi avto "
        "atmen boladi ⛔</blockquote>\n\n"
        "🎁 Konkursga qo'yilgan yutuqlar <tg-spoiler>Hozircha sir🤫</tg-spoiler>\n\n"
        "<blockquote>➕ Konkursga qo'shilish uchun quyidagi tugmani bosing 👇</blockquote>"
    )
    
    bot_info = await message.bot.get_me()
    battle_msg = await message.answer(
        text=battle_text,
        reply_markup=get_battle_kb([], bot_info.username),
        parse_mode="HTML"
    )
    
    LAST_BATTLE_POST["chat_id"] = message.chat.id
    LAST_BATTLE_POST["message_id"] = battle_msg.message_id
    try: await message.delete()
    except: pass

@router.callback_query(F.data == "join_contest")
async def join_contest_callback(callback: types.CallbackQuery):
    username = callback.from_user.username
    if not username:
        return await callback.answer("⚠️ Botdan foydalanish uchun telegram username o'rnating!", show_alert=True)
    
    if add_candidate_to_db(username, None):
        await callback.answer("✅ Siz muvaffaqiyatli ro'yxatga qo'shildingiz!", show_alert=True)
        bot_info = await callback.bot.get_me()
        await callback.message.edit_reply_markup(
            reply_markup=get_battle_kb(get_all_candidates(), bot_info.username)
        )
    else:
        await callback.answer("❌ Siz allaqachon ro'yxatda borasiz!", show_alert=True)

# --- 3. REPLI MENYU TUGMALARI (BARCHA 5 TA BO'LIM) ---
@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_btn(message: types.Message):
    await message.answer("🎡 <b>Baraban o'yini:</b>\nPastdagi tugma orqali o'yinga kiring va omadingizni sinab ko'ring!", 
                         reply_markup=section_inline_kb(url="https://barabandev.netlify.app/"))

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_btn(message: types.Message):
    await message.answer("✌️ <b>Tic-Tac-Toe (Enik-Benik):</b>\nDo'stlaringiz bilan aqlli o'yin o'ynang!", 
                         reply_markup=enik_benik_inline_kb(url="https://tictac-by-tolib.netlify.app/"))

@router.message(F.text == "🎤 Ovozli Batl")
async def voice_battle_btn(message: types.Message):
    bot_info = await message.bot.get_me()
    text = (
        "🎤 <b>Ovozli Batl bo'limi</b>\n\n"
        "Batl boshlash uchun:\n"
        "1. Botni kanalingizga admin qiling.\n"
        "2. Kanalga <code>#konkursx</code> so'zini yuboring.\n"
        "3. Bot avtomatik batl postini yaratadi."
    )
    await message.answer(text, reply_markup=voice_battle_kb(bot_info.username))

@router.message(F.text == "🚀 Yangi Battle (Beta)")
async def create_new_battle_btn(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("📝 <b>Yangi Battle uchun asosiy matnni yuboring:</b>")
        await state.set_state(AdminStates.waiting_for_battle_text)
    else:
        await message.answer("🚫 Bu funksiya faqat adminlar uchun!")

@router.message(F.text == "⚙️ Admin Panel")
async def admin_btn(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("⚙️ <b>Admin boshqaruv paneli:</b>", reply_markup=admin_menu_kb())

# --- 4. YANGI BATTLE (BETA) MANTIQI ---
@router.message(AdminStates.waiting_for_battle_text)
async def process_b_text(message: types.Message, state: FSMContext):
    await state.update_data(b_text=message.text)
    await message.answer("🆔 <b>Battle yuboriladigan kanal @username yuboring:</b>\n(Masalan: @kanalingiz)")
    await state.set_state(AdminStates.waiting_for_battle_channel)

@router.message(AdminStates.waiting_for_battle_channel)
async def finalize_battle_logic(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]])
    try:
        await message.bot.send_message(chat_id=message.text, text=data['b_text'], reply_markup=kb)
        await message.answer("✅ Yangi battle muvaffaqiyatli kanalga yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    await state.clear()

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    username = callback.from_user.username or callback.from_user.first_name
    if add_candidate_to_db(username, callback.message.chat.id):
        caption = f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{username}\n\n📈 <b>OVOZLAR: 0</b>"
        new_post = await callback.bot.send_message(chat_id=callback.message.chat.id, text=caption, reply_to_message_id=callback.message.message_id)
        update_candidate_post_id(username, new_post.message_id)
        await callback.answer("Siz battlega qo'shildingiz!", show_alert=True)
    else:
        await callback.answer("Siz allaqachon qatnashyapsiz!", show_alert=True)

# --- 5. NATIJALAR ---
@router.callback_query(F.data == "results")
async def show_results(callback: types.CallbackQuery):
    candidates = get_all_candidates()
    if not candidates:
        return await callback.answer("Hozircha hech kim qo'shilmagan!", show_alert=True)
    
    res = "📊 <b>Hozirgi natijalar:</b>\n\n"
    for i, c in enumerate(candidates, 1):
        res += f"{i}. @{c['username']} — {c['votes']} ovoz\n"
    
    await callback.answer(res, show_alert=True)
