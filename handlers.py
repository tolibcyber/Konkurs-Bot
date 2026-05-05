import sqlite3
import asyncio
import logging
from datetime import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# O'zingning fayllaringdan importlar
from keyboard import *
from database import (
    add_user, ADMIN_ID, get_total_users, 
    get_all_user_ids, add_channel, remove_channel, get_channels
)

router = Router()
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}
REQUIRED_CHANNEL = "@TolibTokyo"

# --- ADMIN HOLATLARI ---
class AdminStates(StatesGroup):
    waiting_for_ad = State()
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

# --- BAZA FUNKSIYALARI ---
def add_candidate_to_db(username, chat_id=None):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO candidates (username, votes, chat_id) VALUES (?, ?, ?)", 
            (username, 0, chat_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE candidates ADD COLUMN chat_id TEXT")
        cursor.execute("INSERT INTO candidates (username, votes, chat_id) VALUES (?, ?, ?)", (username, 0, chat_id))
        conn.commit()
        return True
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

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- #konkursx (TO'LIQ VA ASL MATN BILAN) ---
@router.channel_post(F.text.contains("#konkursx"))
@router.message(F.text.contains("#konkursx"))
async def start_contest_in_channel(message: types.Message):
    if message.chat.type not in ["channel", "group", "supergroup"]:
        return

    try: await message.delete()
    except: pass

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates"); cursor.execute("DELETE FROM votes")
    conn.commit(); conn.close()

    # Sening asl matning - 100% o'zgarmadi
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
    
    battle_msg = await message.answer(
        text=battle_text,
        reply_markup=get_battle_kb([], (await message.bot.get_me()).username),
        parse_mode="HTML"
    )
    
    LAST_BATTLE_POST["chat_id"] = message.chat.id
    LAST_BATTLE_POST["message_id"] = battle_msg.message_id

# --- START HANDLER ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username) 

    if not await is_subscribed(message.bot, user_id):
        args = command.args or "none"
        return await message.answer(
            f"👋 <b>Assalomu alaykum!</b>\n\nBotdan foydalanish uchun kanalga a'zo bo'ling.",
            reply_markup=sub_keyboard(REQUIRED_CHANNEL, args), parse_mode="HTML"
        )

    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM votes WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return await message.answer("🚫 Siz allaqachon ovoz berib bo'lgansiz!")

        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE username = ?", (candidate,))
        conn.commit(); conn.close()
        
        await message.answer(f"✅ @{candidate} uchun ovozingiz muvaffaqiyatli qabul qilindi!")
        
        if LAST_BATTLE_POST["message_id"]:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=LAST_BATTLE_POST["chat_id"],
                    message_id=LAST_BATTLE_POST["message_id"],
                    reply_markup=get_battle_kb(get_all_candidates(), (await message.bot.get_me()).username)
                )
            except: pass
        return

    # Asl salomlashish matni
    await message.answer(
        f"👋 Salom {message.from_user.first_name}\n\nPastdagi menyudan o'zingizga kerakli bo'limni tanlang:",
        reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML"
    )

# --- REPLY TUGMALAR (ASL MATNLAR BILAN) ---
@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_btn(message: types.Message):
    await message.answer("🎡 <b>Omadingizni sinab ko'rish uchun pastdagi tugmani bosing:</b>", reply_markup=section_inline_kb(url="https://barabandev.netlify.app/"), parse_mode="HTML")

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_btn(message: types.Message):
    await message.answer("<b>✌️ Enik-Benik (Tic-Tac-Toe) o'yini!</b>\n\nDo'stlaringiz bilan o'ynang va g'olib bo'ling!", reply_markup=enik_benik_inline_kb(url="https://tictac-by-tolib.netlify.app/"), parse_mode="HTML")

@router.message(F.text == "🎤 Ovozli Batl")
async def voice_battle_btn(message: types.Message):
    bot_info = await message.bot.get_me()
    # Ovozli batl tushunchasi
    await message.answer(
        "🎤 <b>Ovozli Batl (Konkurs) qo'llanmasi:</b>\n\n"
        "1️⃣ Avval botni kanalingizga admin qiling.\n"
        "2️⃣ Kanalingizga <code>#konkursx</code> xabarini yuboring.\n"
        "3️⃣ Bot avtomatik ravishda batl postini yaratadi.\n\n"
        "Ishtirokchilar username orqali qo'shiladi va ovoz to'playdi!", 
        reply_markup=voice_battle_kb(bot_info.username), 
        parse_mode="HTML"
    )

@router.message(F.text == "⚙️ Admin Panel")
async def admin_btn(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("<b>⚙️ Admin Paneliga xush kelibsiz!</b>\n\nKerakli amalni tanlang:", reply_markup=admin_menu_kb(), parse_mode="HTML")

# --- CALLBACKS ---
@router.callback_query(F.data == "join_contest")
async def join_contest_callback(callback: types.CallbackQuery):
    username = callback.from_user.username
    if not username: return await callback.answer("⚠️ Botda qatnashish uchun avval Telegram sozlamalaridan Username o'rnating!", show_alert=True)
    
    if add_candidate_to_db(username):
        await callback.message.edit_reply_markup(reply_markup=get_battle_kb(get_all_candidates(), (await callback.bot.get_me()).username))
        await callback.answer("✅ Muvaffaqiyatli ro'yxatga qo'shildingiz! Do'stlaringizni ovoz berishga chaqiring.", show_alert=True)
    else:
        await callback.answer("❌ Siz allaqachon ro'yxatda mavjudsiz!", show_alert=True)

@router.callback_query(F.data == "results")
async def results_callback(callback: types.CallbackQuery):
    candidates = get_all_candidates()
    if not candidates:
        return await callback.answer("Hozircha ishtirokchilar yo'q!", show_alert=True)
    
    res_txt = "📊 <b>Hozirgi natijalar:</b>\n\n"
    for i, c in enumerate(candidates):
        res_txt += f"{i+1}. @{c['username']} — <b>{c['votes']}</b> ta ovoz ✅\n"
    
    await callback.answer(res_txt.replace("<b>", "").replace("</b>", ""), show_alert=True)

# --- YANGI BATTLE (BETA) ---
@router.message(F.text == "🚀 Yangi Battle (Beta)")
async def create_new_battle(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("📝 <b>Battle uchun asosiy matnni yuboring:</b>\n\n(Masalan: Kimning ovozi ko'proq?)")
        await state.set_state(AdminStates.waiting_for_battle_text)

@router.message(AdminStates.waiting_for_battle_text)
async def process_b_text(message: types.Message, state: FSMContext):
    await state.update_data(b_text=message.text)
    await message.answer("🆔 <b>Battle yuboriladigan kanal @username'ini yuboring:</b>\n\n(Masalan: @kanalingiz)")
    await state.set_state(AdminStates.waiting_for_battle_channel)

@router.message(AdminStates.waiting_for_battle_channel)
async def finalize_battle(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]])
    try:
        sent_msg = await message.bot.send_message(chat_id=message.text, text=data['b_text'], reply_markup=kb, parse_mode="HTML")
        LAST_BATTLE_POST["chat_id"] = sent_msg.chat.id
        LAST_BATTLE_POST["message_id"] = sent_msg.message_id
        await message.answer("✅ Yangi battle muvaffaqiyatli kanalga joylandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
    await state.clear()

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    username = callback.from_user.username or callback.from_user.first_name
    if add_candidate_to_db(username, callback.message.chat.id):
        participant_text = f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{username}\n\n📈 <b>UMUMIY OVOZLAR: 0</b>"
        new_post = await callback.bot.send_message(chat_id=callback.message.chat.id, text=participant_text, reply_to_message_id=callback.message.message_id, parse_mode="HTML")
        update_candidate_post_id(username, new_post.message_id)
        await callback.answer("Siz battlega qo'shildingiz! Post ostida ovoz to'plang.", show_alert=True)
    else:
        await callback.answer("Siz allaqachon ushbu battleda qatnashyapsiz!", show_alert=True)
