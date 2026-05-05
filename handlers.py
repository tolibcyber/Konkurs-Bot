import sqlite3
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import asyncio
from datetime import datetime
# ... qolgan importlar
from keyboard import *
from database import (
    add_user, ADMIN_ID, get_total_users, 
    get_all_user_ids, add_channel, remove_channel, get_channels
)

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

# --- 1. BAZA FUNKSIYALARI ---
def add_candidate_to_db(username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username, votes) VALUES (?, ?)", (username, 0))
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
    cursor.execute("SELECT username, votes FROM candidates ORDER BY votes DESC")
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
        res_txt += f"{i}. @{c['username']} — {c['votes']} ovoz\n"
    
    await callback.answer(res_txt, show_alert=True)
    user_status = await callback.bot.get_chat_member(chat_id=callback.message.chat.id, user_id=callback.from_user.id)
    
    if str(callback.from_user.id) == str(ADMIN_ID) or user_status.status in ["administrator", "creator"]:
        top_5 = candidates[:5]
        top_txt = "🔥 <b>TOP 5 G'oliblar Natijalari:</b>\n\n"
        for i, c in enumerate(top_5, 1):
            top_txt += f"{i}️⃣ @{c['username']} — {c['votes']} ta ovoz\n"
        top_txt += "\n🏆 <i>G'oliblik sari olg'a!</i>"
        try:
            await callback.message.answer(top_txt, parse_mode="HTML")
        except: pass

@router.callback_query(F.data == "join_contest")
async def join_callback(callback: types.CallbackQuery):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        return await callback.answer("Konkursda qatnashish uchun kanalga obuna bo'ling!", show_alert=True)

    username = callback.from_user.username
    if not username:
        return await callback.answer("Username o'rnating!", show_alert=True)
    
    if add_candidate_to_db(username):
        candidates = get_all_candidates()
        bot_info = await callback.bot.get_me() # message.bot o'rniga callback.bot
        await callback.message.edit_reply_markup(
            reply_markup=get_battle_kb(candidates, bot_info.username)
        )
        await callback.answer("Muvaffaqiyatli ro'yxatga qo'shildingiz!", show_alert=True)
    else:
        await callback.answer("Siz allaqachon ro'yxatdasiz!", show_alert=True)

@router.callback_query(F.data == "join_new_battle")
async def join_new_battle_handler(callback: types.CallbackQuery):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        return await callback.answer("Avval kanalga obuna bo'ling!", show_alert=True)

    username = callback.from_user.username or callback.from_user.first_name
    
    # Ishtirokchi posti (Reply qilib)
    participant_text = f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{username}\n\n❤️ Reaksiyalar: 0/100\n💬 Komentlar: 0/100\n⭐ Stars: 0\n\n📈 <b>UMUMIY BALL: 0</b>"

    new_post = await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=participant_text,
        reply_to_message_id=LAST_BATTLE_POST["message_id"],
        parse_mode="HTML"
    )
    
    if add_candidate_to_db(username, callback.message.chat.id):
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
    # Bu tugmani hamma bosa oladi, lekin faqat admin boshqara oladi
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("📝 Battle uchun asosiy matnni kiriting (Kanalda chiqadi):")
        await state.set_state(AdminStates.waiting_for_battle_text)
    else:
        await message.answer("Siz ham o'z kanalingizda shunday battle o'tkazmoqchimisiz? Botni kanalga admin qiling va #battle deb yozing!")

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
    
    sent_msg = await message.bot.send_message(chat_id=channel, text=data['b_text'], reply_markup=kb, parse_mode="HTML")
    LAST_BATTLE_POST["chat_id"] = sent_msg.chat.id
    LAST_BATTLE_POST["message_id"] = sent_msg.message_id
    
    await message.answer(f"✅ Battle kanalga yuborildi!")
    await state.clear()

LAST_BATTLE_POST = {"chat_id": None, "message_id": None}
# Bu o'zgarmaydi, lekin pastdagi funksiyalarda ishlatamiz.

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

# --- 2-QISM: AVTO-YANGILASH MOTORU ---

async def auto_update_scores(bot: Bot):
    """Har 5 daqiqada barcha kanallardagi ballarni yangilab chiqadi"""
    while True:
        try:
            await asyncio.sleep(300) # 300 soniya = 5 daqiqa
            candidates = get_all_candidates()
            
            if not candidates:
                continue

            for c in candidates:
                chat_id = c.get('chat_id')
                post_id = c.get('post_id')
                
                if not chat_id or not post_id:
                    continue
                
                votes = c.get('votes', 0)
                # Xabar matni (o'zing xohlagandek tahrirlashing mumkin)
                updated_text = (
                    f"🏆 <b>BATTLE ISHTIROKCHISI:</b> @{c['username']}\n\n"
                    f"📊 <b>Ballar holati:</b>\n"
                    f"✅ Ovozlar: {votes}\n"
                    f"📈 <b>UMUMIY BALL: {votes}</b>\n"
                    f"──────────────────\n"
                    f"🕒 Yangilandi: {datetime.now().strftime('%H:%M')}"
                )
                
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=post_id,
                        text=updated_text,
                        parse_mode="HTML"
                    )
                except Exception:
                    # Agar xabar o'zgarmagan bo'lsa yoki bot kanaldan haydalgan bo'lsa xatoni o'tkazib yuboradi
                    continue
                    
        except Exception as e:
            logging.error(f"Avto-yangilashda xato: {e}")
            await asyncio.sleep(10)
