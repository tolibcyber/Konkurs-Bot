import sqlite3
import asyncio
import logging
from datetime import datetime

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# O'zing yaratgan fayllardan importlar
from keyboard import *
from database import (
    add_user, ADMIN_ID, get_total_users, 
    update_candidate_post_id, add_candidate_to_db,
    get_all_user_ids, add_channel, remove_channel, 
    get_channels, init_db, get_all_candidates,
    add_commenter, get_unique_comments_count # <--- Bularni qo'shdik
)

router = Router()
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}
REQUIRED_CHANNEL = "@TolibTokyo"

# --- BARCHA HOLATLAR BITTA KLASSDA ---
class AdminStates(StatesGroup):
    waiting_for_ad = State()
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

# --- TEKSHIRUV FUNKSIYASI ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- 1. OVOZLI BATL (#konkursx) ---
@router.channel_post(F.text.contains("#konkursx"))
@router.message(F.text.contains("#konkursx"))
async def start_contest_in_channel(message: types.Message):
    if message.chat.type not in ["channel", "group", "supergroup"]:
        return
    try: await message.delete()
    except: pass

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM votes")
    conn.commit(); conn.close()

    candidates = get_all_candidates()
    battle_text = (
        f"<b>{message.chat.title}</b> 🧸\n"
        "🏆 <b>BATL Boshlandi</b>🥳\n\n"
        "➕ Konkursga qo'shilish uchun quyidagi tugmani bosing 👇"
    )
    battle_msg = await message.answer(
        text=battle_text,
        reply_markup=get_battle_kb(candidates, (await message.bot.get_me()).username),
        parse_mode="HTML"
    )
    LAST_BATTLE_POST["chat_id"] = message.chat.id
    LAST_BATTLE_POST["message_id"] = battle_msg.message_id

# --- 2. START HANDLER ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username) 

    args = command.args
    if args and args.startswith("vote_"):
        if not await is_subscribed(message.bot, user_id):
            return await message.answer("Ovoz berish uchun avval kanalga a'zo bo'ling!", 
                                       reply_markup=sub_keyboard(REQUIRED_CHANNEL, args))

        candidate = "@" + args.replace("vote_", "")
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM votes WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return await message.answer("🚫 Siz allaqachon ovoz bergansiz!")

        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE username = ?", (candidate,))
        conn.commit(); conn.close()
        
        await message.answer(f"✅ {candidate} uchun ovozingiz qabul qilindi!")
        
        if LAST_BATTLE_POST["message_id"]:
            candidates = get_all_candidates()
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=LAST_BATTLE_POST["chat_id"],
                    message_id=LAST_BATTLE_POST["message_id"],
                    reply_markup=get_battle_kb(candidates, (await message.bot.get_me()).username)
                )
            except: pass
        return

    await message.answer("👋 Salom! Kerakli bo'limni tanlang:", 
                         reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 3. REPLAY TUGMALAR (Baraban, Enik-Benik, Ovozli Batl) ---
@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_reply_btn(message: types.Message):
    if not await is_subscribed(message.bot, message.from_user.id):
        return await message.answer("Avval kanalga a'zo bo'ling!", reply_markup=sub_keyboard(REQUIRED_CHANNEL, "none"))
    await message.answer("🎡 Baraban o'yini:", reply_markup=section_inline_kb(url="https://barabandev.netlify.app/"))

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_reply_btn(message: types.Message):
    if not await is_subscribed(message.bot, message.from_user.id):
        return await message.answer("Avval kanalga a'zo bo'ling!", reply_markup=sub_keyboard(REQUIRED_CHANNEL, "none"))
    await message.answer("✌️ Enik-Benik:", reply_markup=enik_benik_inline_kb(url="https://tictac-by-tolib.netlify.app/"))

@router.message(F.text == "🎤 Ovozli Batl")
async def voice_battle_reply_btn(message: types.Message):
    bot_info = await message.bot.get_me()
    await message.answer("🎤 Ovozli Batl bo'yicha qo'llanma...", reply_markup=voice_battle_kb(bot_info.username), parse_mode="HTML")

# --- 4. YANGI BATTLE (BETA) ---
@router.message(F.text == "🚀 Yangi Battle (Beta)")
async def create_new_battle(message: types.Message, state: FSMContext):
    await message.answer("<b>Yangi Battle yaratish</b> 🚀\nMatnni yuboring:")
    await state.set_state(AdminStates.waiting_for_battle_text)

@router.message(AdminStates.waiting_for_battle_text)
async def process_b_text(message: types.Message, state: FSMContext):
    await state.update_data(b_text=message.text)
    await message.answer("🆔 Kanal @username'sini kiriting:")
    await state.set_state(AdminStates.waiting_for_battle_channel)

@router.message(AdminStates.waiting_for_battle_channel)
async def finalize_battle(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel = message.text
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Qatnashish", callback_data="join_new_battle")]])
    try:
        sent_msg = await message.bot.send_message(chat_id=channel, text=data['b_text'], reply_markup=kb)
        LAST_BATTLE_POST["chat_id"] = sent_msg.chat.id
        LAST_BATTLE_POST["message_id"] = sent_msg.message_id
        await message.answer(f"✅ Battle boshlandi!")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

# --- 5. KOMMENTLARNI TUTUVCHI HANDLER ---
@router.message(F.reply_to_message)
async def track_comments(message: types.Message):
    if message.reply_to_message:
        main_post_id = message.reply_to_message.message_id
        user_id = message.from_user.id
        add_commenter(main_post_id, user_id)

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        return await callback.answer("Avval kanalga obuna bo'ling! 📢", show_alert=True)
    
    user = callback.from_user
    username = f"@{user.username}" if user.username else user.first_name
    
    # Ishtirokchi posti (Hozircha 0 ballar bilan)
    participant_text = (
        f"🏆 <b>BATTLE ISHTIROKCHISI:</b> {username}\n\n"
        f"❤️ Reaksiyalar: 0/100 (+0 ball)\n"
        f"💬 Komentlar: 0/50 (+0 ball)\n"
        f"⭐ Stars: 0/∞ (+0 ball)\n\n"
        f"📈 <b>UMUMIY BALL: 0</b>"
    )
    
    try:
        new_post = await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=participant_text,
            reply_to_message_id=callback.message.message_id,
            parse_mode="HTML"
        )
        if add_candidate_to_db(username, callback.message.chat.id):
            update_candidate_post_id(username, new_post.message_id)
            await callback.answer("Qo'shildingiz! ✅", show_alert=True)
    except:
        await callback.answer("Xatolik! ❌", show_alert=True)

# --- 6. ADMIN PANEL VA REKLAMA ---
@router.message(F.text == "⚙️ Admin Panel")
async def admin_reply_btn(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("⚙️ Admin Panel:", reply_markup=admin_menu_kb())

@router.callback_query(F.data == "results")
async def results_callback(callback: types.CallbackQuery):
    candidates = get_all_candidates()
    res_txt = "📊 Natijalar:\n\n"
    for i, c in enumerate(candidates, 1):
        res_txt += f"{i}. {c['username']} — {c['votes']} ovoz\n"
    await callback.answer(res_txt, show_alert=True)
