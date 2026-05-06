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
    add_user, 
    ADMIN_ID, 
    get_total_users, 
    update_candidate_post_id,
    add_candidate_to_db,
    get_all_user_ids, 
    add_channel, 
    remove_channel, 
    get_channels,
    init_db  # Agar kerak bo'lsa
)

# Routerni e'lon qilish
router = Router()

router = Router()
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}
REQUIRED_CHANNEL = "@TolibTokyo"

class AdminStates(StatesGroup):
    waiting_for_ad = State()
    # Shularni davomidan qo'sh:
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

# --- ADMIN PANEL UCHUN HOLATLAR ---
class AdminStates(StatesGroup):
    waiting_for_ad = State()

# --- 1. BAZA FUNKSIYALARI (Tuzatilgan variant) ---
def add_candidate_to_db(username, chat_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        # Username va chat_id birga kelishi kerak
        cursor.execute("INSERT INTO candidates (username, votes, chat_id) VALUES (?, ?, ?)", (username, 0, str(chat_id)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logging.error(f"Baza xatosi: {e}")
        return False
    finally:
        conn.close()

def get_all_candidates():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    # Faqat ovozlar soni bo'yicha saralaymiz
    cursor.execute("SELECT username, votes, chat_id FROM candidates ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- 2. TEKSHIRUV FUNKSIYASI ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- 3. KANALDA KONKURSNI BOSHLASH (#konkursx) ---
@router.channel_post(F.text.contains("#konkursx"))
@router.message(F.text.contains("#konkursx"))
async def start_contest_in_channel(message: types.Message):
    if message.chat.type not in ["channel", "group", "supergroup"]:
        return

    try:
        await message.delete()
    except:
        pass

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM votes")
    conn.commit(); conn.close()

    candidates = get_all_candidates()
    
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
        reply_markup=get_battle_kb(candidates, (await message.bot.get_me()).username),
        parse_mode="HTML"
    )
    
    LAST_BATTLE_POST["chat_id"] = message.chat.id
    LAST_BATTLE_POST["message_id"] = battle_msg.message_id

# --- 4. START VA MAJBURIY OBUNA ---
# --- START: OVOZ BERISH QISMI ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username) 

    args = command.args
    if args and args.startswith("vote_"):
        # Majburiy obunani tekshirish
        if not await is_subscribed(message.bot, user_id):
            return await message.answer("Ovoz berish uchun avval kanalga a'zo bo'ling!", 
                                       reply_markup=sub_keyboard(REQUIRED_CHANNEL, args))

        candidate = "@" + args.replace("vote_", "")
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Allaqachon ovoz berganmi?
        cursor.execute("SELECT * FROM votes WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return await message.answer("🚫 Siz allaqachon ovoz bergansiz!")

        # Ovozni hisoblash
        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE username = ?", (candidate,))
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ {candidate} uchun ovozingiz qabul qilindi!")

        # KANALDA BALLARNI YANGILASH
        if LAST_BATTLE_POST["message_id"]:
            candidates = get_all_candidates()
            bot_me = await message.bot.get_me()
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=LAST_BATTLE_POST["chat_id"],
                    message_id=LAST_BATTLE_POST["message_id"],
                    reply_markup=get_battle_kb(candidates, bot_me.username)
                )
            except: pass
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

# --- 5. REPLY TUGMALAR ---
@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_reply_btn(message: types.Message):
    if not await is_subscribed(message.bot, message.from_user.id):
        return await message.answer("Avval kanalga a'zo bo'ling!", reply_markup=sub_keyboard(REQUIRED_CHANNEL, "none"))
    await message.answer(
        "🎡 <b>Baraban o'yini</b> bo'limini tanladingiz.\n\nOmadingizni sinab ko'rish uchun pastdagi tugmani bosing:",
        reply_markup=section_inline_kb(url="https://barabandev.netlify.app/"),
        parse_mode="HTML"
    )

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_reply_btn(message: types.Message):
    # Majburiy obunani tekshirish (agar kerak bo'lsa)
    if not await is_subscribed(message.bot, message.from_user.id):
        return await message.answer("Avval kanalga a'zo bo'ling!", reply_markup=sub_keyboard(REQUIRED_CHANNEL, "none"))

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
        f"O'z kanalingizda professional darajadagi konkurslarni o'tkazish juda oson!\n\n"
        f"1️⃣ <b>Botni kanalga qo'shish:</b> Pastdagi tugma orqali botni o'z kanalingizga qo'shing va unga <b>Admin</b> huquqini bering.\n\n"
        f"2️⃣ <b>Konkursni boshlash:</b> Bot admin bo'lgan kanalingizga <code>#konkursx</code> kalit so'zini yuboring.\n\n"
        f"3️⃣ <b>Avtomatik post:</b> Bot darhol kanalga chiroyli dizayndagi konkurs postini joylashtiradi.\n\n"
        f"⚠️ <b>Muhim eslatma:</b> Ishtirokchilar 'Qatnashish' tugmasini bosish orqali avtomatik ro'yxatga qo'shiladi.\n\n"
        f"💎 <b>Botning afzalligi:</b> Har bir ovoz beruvchi majburiy obunadan o'tadi!"
    )
    await message.answer(guide_text, reply_markup=voice_battle_kb(bot_info.username), parse_mode="HTML")

@router.message(F.text == "⚙️ Admin Panel")
async def admin_reply_btn(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return await message.answer("Siz admin emassiz! 🚫")
    await message.answer(
        "<b>⚙️ Admin Paneliga xush kelibsiz!</b>\n\nBu yerdan bot statistikasini ko'rishingiz, hamma foydalanuvchilarga reklama yuborishingiz mumkin.",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )

# --- REKLAMA FUNKSIYASI ---
@router.callback_query(F.data == "send_ads")
async def start_ad_sending(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Reklama xabarini yuboring:\n\nMatn, rasm, video yoki forward bo'lishi mumkin. Bekor qilish uchun /cancel yuboring.")
    await state.set_state(AdminStates.waiting_for_ad)
    await callback.answer()

@router.message(AdminStates.waiting_for_ad)
async def process_ad_distribution(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("Reklama yuborish bekor qilindi. ❌")

    user_ids = get_all_user_ids()
    count = 0
    status_msg = await message.answer(f"🚀 Yuborish boshlandi: 0/{len(user_ids)}")
    
    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            count += 1
            if count % 20 == 0:
                await status_msg.edit_text(f"🚀 Yuborilmoqda: {count}/{len(user_ids)}")
            await asyncio.sleep(0.05)
        except: pass
    
    await message.answer(f"✅ Reklama muvaffaqiyatli yakunlandi!\n\nJami: {count} ta foydalanuvchiga yuborildi.")
    await state.clear()

# --- 6. CALLBACKLAR ---
@router.callback_query(F.data.startswith("check_sub_"))
async def check_subscription_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await is_subscribed(callback.bot, user_id):
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", 
                                     reply_markup=main_reply_menu(user_id, ADMIN_ID))
    else:
        await callback.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)

@router.callback_query(F.data == "results")
async def results_callback(callback: types.CallbackQuery):
    candidates = get_all_candidates()
    if not candidates:
        return await callback.answer("Hozircha nomzodlar yo'q!", show_alert=True)
    
    res_txt = "📊 Konkurs natijalari:\n\n"
    for i, c in enumerate(candidates, 1):
        res_txt += f"{i}. {c['username']} — {c['votes']} ovoz\n"
    
    await callback.answer(res_txt, show_alert=True)
    user_status = await callback.bot.get_chat_member(chat_id=callback.message.chat.id, user_id=callback.from_user.id)
    
    if str(callback.from_user.id) == str(ADMIN_ID) or user_status.status in ["administrator", "creator"]:
        top_5 = candidates[:5]
        top_txt = "🔥 <b>TOP 5 G'oliblar</b>\n\n"
        for i, c in enumerate(top_5, 1):
            top_txt += f"{i}️⃣ @{c['username']} — {c['votes']} ta ovoz\n"
        top_txt += "\n🏆 <i>G'oliblik sari olg'a!</i>"
        try:
            await callback.message.answer(top_txt, parse_mode="HTML")
        except: pass

# --- OVOZLI BATL: QATNASHISH VA BALLARNI YANGILASH ---
@router.callback_query(F.data == "join_contest")
async def join_contest_handler(callback: types.CallbackQuery):
    user_username = callback.from_user.username
    
    if not user_username:
        return await callback.answer("Username o'rnating! ⚠️ (Settings -> Username)", show_alert=True)

    username_with_at = f"@{user_username}"
    # Hozirgi xabar (post) qaysi kanalda ekanini olish
    current_chat_id = callback.message.chat.id
    
    # 1. Bazaga qo'shish (chat_id bilan birga)
    added = add_candidate_to_db(username_with_at, current_chat_id)
    
    if added:
        # 2. Yangi ro'yxatni olish
        candidates = get_all_candidates()
        bot_info = await callback.bot.get_me()
        
        # 3. KANALDA BALLARNI VA RO'YXATNI SRAZI YANGILASH
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_battle_kb(candidates, bot_info.username)
            )
            await callback.answer("Tabriklaymiz! Siz ro'yxatga qo'shildingiz va ballar yangilandi. ✅", show_alert=True)
        except Exception as e:
            logging.error(f"Yangilashda xato: {e}")
            await callback.answer("Ro'yxatga qo'shildingiz! 🚀", show_alert=True)
    else:
        await callback.answer("Siz allaqachon ushbu konkursda ishtirok etyapsiz! 😊", show_alert=True)

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        return await callback.answer("Avval kanalga obuna bo'ling!", show_alert=True)

    username = callback.from_user.username or callback.from_user.first_name
    
    # Ishtirokchi posti (Reply qilib)
    participant_text = f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{username}\n\n❤️ Reaksiyalar: +1 ball (100)\n💬 Komentlar: +2 ball (100)\n⭐ Stars: Cheksiz\n\n📈 <b>UMUMIY BALL: 0</b>"

    new_post = await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=participant_text,
        reply_to_message_id=LAST_BATTLE_POST["message_id"],
        parse_mode="HTML"
    )
    
    if add_candidate_to_db(username):
        update_candidate_post_id(username, new_post.message_id)
        await callback.answer("Qo'shildingiz!", show_alert=True)
    else:
        await callback.answer("Siz allaqachon ro'yxatdasiz!", show_alert=True)

# 1. Avval Klassni yozamiz (Funksiyalardan tepada tursin)
class AdminStates(StatesGroup):
    waiting_for_ads = State()
    waiting_for_battle_text = State() # Mana bu to'g'ri joyi
    waiting_for_battle_channel = State() # Buni ham qo'shib qo'y, kanalni so'rash uchun kerak

# 2. Keyin Handler funksiyasi keladi
@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    total_users = get_total_users()
    await callback.message.edit_text(
        text=f"<b>📊 Bot Statistikasi:</b>\n\n👥 Umumiy foydalanuvchilar: <b>{total_users} ta</b>",
        reply_markup=back_to_main_kb(),
        parse_mode="HTML"
    ) # Qavs bu yerda yopilishi kerak!

@router.message(F.text == "🚀 Yangi Battle (Beta)")
async def create_new_battle(message: types.Message, state: FSMContext):
    # Endi bu yerda if str(user_id) == str(ADMIN_ID) tekshiruvi yo'q!
    # Hamma foydalana oladi
    await message.answer(
        "<b>Yangi Battle yaratish bo'limi</b> 🚀\n\n"
        "1️⃣ Avval battle uchun asosiy matnni yuboring (masalan: 'Kim chiroyli rasm chizadi?'):\n\n"
        "<i>Bekor qilish uchun /cancel yuboring.</i>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_battle_text)

@router.message(AdminStates.waiting_for_battle_text)
async def process_b_text(message: types.Message, state: FSMContext):
    await state.update_data(b_text=message.text)
    await message.answer("🆔 Kanal ID yoki @username kiriting (Masalan: @TolibTokyo):")
    await state.set_state(AdminStates.waiting_for_battle_channel)

@router.message(AdminStates.waiting_for_battle_channel)
async def finalize_battle(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel = message.text # Foydalanuvchi yuborgan kanal ID yoki @username
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Battlega qatnashish", callback_data="join_new_battle")]
    ])
    
    try:
        # Bot kanalda adminligini va xabar yubora olishini tekshiramiz
        sent_msg = await message.bot.send_message(
            chat_id=channel, 
            text=data['b_text'], 
            reply_markup=kb, 
            parse_mode="HTML"
        )
        
        # Battle ma'lumotlarini eslab qolamiz
        LAST_BATTLE_POST["chat_id"] = sent_msg.chat.id
        LAST_BATTLE_POST["message_id"] = sent_msg.message_id
        
        await message.answer(f"✅ Battle muvaffaqiyatli boshlandi! \nKanal: {channel}")
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ <b>Xatolik yuz berdi!</b>\n\n"
            f"Botni {channel} kanaliga admin qilganingizga va xabar yuborish huquqi borligiga ishonch hosil qiling.",
            parse_mode="HTML"
        )
        logging.error(f"Battle yaratishda xato: {e}")

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    start_txt = (
        f"👋 Salom {callback.from_user.first_name} \n\n"
        f"Sizni botimizda ko'rib turganimizdan xursandmiz! Bu yerda siz quyidagi imkoniyatlarga egasiz:\n\n"
        f"🎡 <b>Baraban:</b> O'z omadingizni sinab ko'ring va sovg'alar yuting!\n"
        f"✌️ <b>Enik-Benik:</b> Do'stlar bilan qiziqarli o'yinlar o'ynang!\n"
        f"🎤 <b>Ovozli Batl:</b> O'z kanalingizda professional konkurslar tashkil qiling!\n\n"
        f"🚀 <b>Pastdagi menyudan o'zingizga kerakli bo'limni tanlang:</b>"
    )
    try:
        await callback.message.edit_text(text=start_txt, reply_markup=None, parse_mode="HTML")
        await callback.answer() 
    except:
        await callback.message.answer(start_txt, reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML")
        await callback.answer()

# --- 1-QISM: MULTI-KANAL UCHUN BAZA FUNKSIYALARI ---

def add_candidate_to_db(username, chat_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        # chat_id - bu nomzod qaysi kanalda ekanligini bildiradi
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
    # post_id va chat_id avto-yangilash uchun juda muhim
    cursor.execute("SELECT username, votes, post_id, chat_id FROM candidates ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


