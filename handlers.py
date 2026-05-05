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

# database.py dan kerakli funksiyalarni import qilish
from database import (
    add_user, ADMIN_ID, get_total_users, 
    get_all_user_ids, add_channel, remove_channel, get_channels
)

router = Router()
REQUIRED_CHANNEL = "@TolibTokyo"

# --- HOLATLAR ---
class AdminStates(StatesGroup):
    waiting_for_ad = State()
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

# --- 1. BAZA FUNKSIYALARI (Universal variant) ---
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
            f"Botimizdan foydalanish uchun kanalimizga obuna bo'ling.\n\n"
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
            return await message.answer("🚫 Siz allaqachon ovoz berib bo'lgansiz!", parse_mode="HTML")

        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE username = ?", (candidate,))
        conn.commit(); conn.close()
        
        await message.answer(f"✅ @{candidate} uchun ovozingiz qabul qilindi!")
        return

    start_txt = (
        f"👋 Salom {message.from_user.first_name} \n\n"
        f"🎡 <b>Baraban:</b> Ism yozib g'olib aniqlang!\n"
        f"✌️ <b>Enik-Benik:</b> Tic-Tac-Toe (X-O) o'yini!\n"
        f"🎤 <b>Ovozli Batl:</b> Konkurslar tashkil qiling!\n\n"
        f"🚀 <b>Kerakli bo'limni tanlang:</b>"
    )
    await message.answer(start_txt, reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 4. O'YINLAR (BARABAN, ENIK-BENIK, VOICE) ---
@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_reply_btn(message: types.Message):
    await message.answer("🎡 <b>Baraban o'yini:</b>", reply_markup=section_inline_kb(url="https://barabandev.netlify.app/"), parse_mode="HTML")

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_reply_btn(message: types.Message):
    await message.answer("<b>✌️ Enik-Benik: Tic-Tac-Toe</b>", reply_markup=enik_benik_inline_kb(url="https://tictac-by-tolib.netlify.app/"), parse_mode="HTML")

@router.message(F.text == "🎤 Ovozli Batl")
async def voice_battle_reply_btn(message: types.Message):
    bot_info = await message.bot.get_me()
    guide_text = (
        f"🎤 <b>Ovozli Batl qo'llanmasi:</b>\n\n"
        f"1️⃣ Botni kanalga Admin qiling.\n"
        f"2️⃣ <b>#konkursx</b> yoki <b>🚀 Yangi Battle</b> orqali boshlang.\n"
        f"3️⃣ Har bir ovoz beruvchi {REQUIRED_CHANNEL} kanaliga a'zo bo'lishi shart!"
    )
    await message.answer(guide_text, reply_markup=voice_battle_kb(bot_info.username), parse_mode="HTML")

# --- 5. YANGI BATTLE TIZIMI (UNIVERSAL) ---
@router.message(F.text == "🚀 Yangi Battle (Beta)")
async def create_new_battle(message: types.Message, state: FSMContext):
    await message.answer("📝 Battle uchun asosiy matnni kiriting:")
    await state.set_state(AdminStates.waiting_for_battle_text)

@router.message(AdminStates.waiting_for_battle_text)
async def process_b_text(message: types.Message, state: FSMContext):
    await state.update_data(b_text=message.text)
    await message.answer("🆔 Kanal ID yoki @username kiriting:")
    await state.set_state(AdminStates.waiting_for_battle_channel)

@router.message(AdminStates.waiting_for_battle_channel)
async def finalize_battle(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel = message.text
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]])
    
    try:
        await message.bot.send_message(chat_id=channel, text=data['b_text'], reply_markup=kb, parse_mode="HTML")
        await message.answer(f"✅ Battle kanalga yuborildi!")
    except:
        await message.answer("❌ Xato! Bot kanalda admin emas.")
    await state.clear()

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        return await callback.answer("Avval kanalga obuna bo'ling!", show_alert=True)

    username = callback.from_user.username or callback.from_user.first_name
    participant_text = f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{username}\n\n📈 <b>UMUMIY BALL: 0</b>"

    try:
        new_post = await callback.bot.send_message(chat_id=callback.message.chat.id, text=participant_text, parse_mode="HTML")
        if add_candidate_to_db(username, callback.message.chat.id):
            update_candidate_post_id(username, new_post.message_id)
            await callback.answer("Qo'shildingiz!", show_alert=True)
        else:
            await callback.answer("Siz allaqachon ro'yxatdasiz!", show_alert=True)
    except:
        await callback.answer("Xatolik!", show_alert=True)

# --- 6. AVTO-YANGILASH MOTORU ---
async def auto_update_scores(bot: Bot):
    while True:
        try:
            await asyncio.sleep(300)
            candidates = get_all_candidates()
            for c in candidates:
                if not c['chat_id'] or not c['post_id']: continue
                
                updated_text = (
                    f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{c['username']}\n\n"
                    f"📊 <b>Ballar holati:</b>\n✅ Ovozlar: {c['votes']}\n"
                    f"📈 <b>UMUMIY BALL: {c['votes']}</b>\n"
                    f"──────────────────\n🕒 {datetime.now().strftime('%H:%M')}"
                )
                try:
                    await bot.edit_message_text(chat_id=c['chat_id'], message_id=c['post_id'], text=updated_text, parse_mode="HTML")
                except: continue
        except Exception as e:
            await asyncio.sleep(10)

# --- ADMIN PANEL VA CALLBACKLAR ---
@router.message(F.text == "⚙️ Admin Panel")
async def admin_reply_btn(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    await message.answer("<b>⚙️ Admin Panel</b>", reply_markup=admin_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data.startswith("check_sub_"))
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.bot, callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi!", reply_markup=main_reply_menu(callback.from_user.id, ADMIN_ID))
    else:
        await callback.answer("❌ Obuna bo'lmagansiz!", show_alert=True)

@router.callback_query(F.data == "results")
async def results_callback(callback: types.CallbackQuery):
    candidates = get_all_candidates()
    res_txt = "📊 Natijalar:\n\n" + "\n".join([f"{i+1}. @{c['username']} — {c['votes']}" for i, c in enumerate(candidates)])
    await callback.answer(res_txt, show_alert=True)
