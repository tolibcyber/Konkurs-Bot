from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
import sqlite3
from database import ADMIN_ID, get_top_candidates 
from keyboard import main_menu, get_battle_kb

router = Router()

# --- 1. START XABARI (O'SHA SEN SOG'INGAN TO'LIQ VARIANT) ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    
    # REFERAL ORQALI OVOZ BERISH
    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # FOYDALANUVCHI OLDIN OVOZ BERGANMI?
        cursor.execute("SELECT candidate_username FROM votes WHERE user_id = ?", (user_id,))
        check_vote = cursor.fetchone()

        if check_vote:
            conn.close()
            return await message.answer(
                "🚫 <b>Kechirasiz, qoidabuzarlik!</b>\n\nSiz tizimda allaqachon ovoz bergansiz. "
                "Konkurs shaffofligini ta'minlash maqsadida bir foydalanuvchi faqat 1 marta ovoz bera oladi. "
                "Adolatli o'yin tarafdori bo'lganingiz uchun rahmat!", 
                parse_mode="HTML"
            )

        # OVOZNI QABUL QILISH
        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes_count = votes_count + 1 WHERE username = ?", (candidate,))
        conn.commit()
        conn.close()
        
        return await message.answer(
            f"✅ <b>Tabriklaymiz!</b>\n\nSiz @{candidate} uchun muvaffaqiyatli ovoz berdingiz. "
            f"Siz kabi faol do'stlarimiz borligidan xursandmiz! Omad yor bo'lsin!", 
            parse_mode="HTML"
        )

    # ODDIY START XABARI
    start_text = (
        f"🌟 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        f"Sizni professional tanlovlar va qiziqarli o'yinlar botida ko'rib turganimizdan mamnunmiz. "
        f"Bu yerda siz nafaqat ko'ngilochar o'yinlar o'ynashingiz, balki qimmatbaho sovg'alar "
        f"yutib olishingiz mumkin bo'lgan batllarda qatnashishingiz mumkin.\n\n"
        f"🚀 <b>Tanlovingizni pastdagi menyu orqali amalga oshiring:</b>"
    )
    await message.answer(start_text, reply_markup=main_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 2. OVOZLI BATL (KONKURS XABARI) ---
@router.message(F.text == "🎤 Ovozli Batl")
async def battle_starter(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): 
        return

    bot_info = await message.bot.get_me()
    battle_text = (
        "🏆 <b>DIQQAT, KONKURS BOSHLANDI!</b> 🥳\n\n"
        "Aziz kuzatuvchilar, bizning navbatdagi tanlovimizga start berildi! "
        "G'olib bo'lish va o'z kuchingizni ko'rsatish vaqti keldi.\n\n"
        "❕ <b>Ishtirok etish shartlari:</b>\n"
        "1️⃣ Pastdagi tugma orqali ro'yxatdan o'ting.\n"
        "2️⃣ Sizga beriladigan maxsus havola orqali do'stlaringizni chaqiring.\n"
        "3️⃣ Eng ko'p ovoz to'plang va g'oliblikni qo'lga kiriting!\n\n"
        "<blockquote>🚫 <b>Eslatma:</b> Bir foydalanuvchi faqat 1 marta ovoz bera oladi. Barcha jarayonlar bot tomonidan nazorat qilinadi.</blockquote>\n\n"
        "👇 <b>Tanlovda qatnashish uchun bosing:</b>"
    )
    await message.answer(battle_text, reply_markup=get_battle_kb(bot_info.username), parse_mode="HTML")

# --- 3. KONKURSGA QO'SHILISH (CALLBACK) ---
@router.callback_query(F.data == "join_contest")
async def join_callback(callback: types.CallbackQuery):
    user_username = callback.from_user.username
    if not user_username:
        return await callback.answer("❌ Xatolik: Profilingizda username yo'q!", show_alert=True)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username) VALUES (?)", (user_username,))
        conn.commit()
        
        bot_info = await callback.bot.get_me()
        share_url = f"https://t.me/{bot_info.username}?start=vote_{user_username}"
        
        await callback.message.answer(
            f"🎉 <b>Tabriklaymiz, siz ro'yxatdasiz!</b>\n\n"
            f"Sizning shaxsiy havolangiz:\n<code>{share_url}</code>\n\n"
            f"Ushbu havolani do'stlaringizga yuboring. Kim eng ko'p ovoz to'plasa, o'sha g'olib! 🔥",
            parse_mode="HTML"
        )
    except sqlite3.IntegrityError:
        await callback.answer("😊 Siz allaqachon ishtirokchilar orasida borsiz.", show_alert=True)
    finally:
        conn.close()

# --- 4. NATIJALAR (TOP 5) ---
@router.message(F.text == "📊 Natijalar")
async def results_handler(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): 
        return

    results = get_top_candidates(5)
    if not results:
        return await message.answer("📊 <b>Hozircha faol ishtirokchilar mavjud emas.</b>", parse_mode="HTML")

    msg = "📊 <b>CURRENT TOP 5 RANKING</b>\n🏆 <b>Eng kuchli nomzodlar ro'yxati:</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, (name, count) in enumerate(results):
        msg += f"<blockquote>{medals[i]} @{name} — <b>{count}</b> ta ovoz</blockquote>\n\n"
    
    await message.answer(msg + "✨ <i>Natijalar real vaqt rejimida yangilanib boradi.</i>", parse_mode="HTML")
