from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
import sqlite3
from database import ADMIN_ID, get_top_candidates # database.py dan kerakli o'zgaruvchilarni olamiz

router = Router()

# --- 1. START XABARI (TO'LIQ) ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    
    # OVOZ BERISH MANTIQI (REFERAL LINK ORQALI)
    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        # Foydalanuvchi oldin ovoz berganmi?
        cursor.execute("SELECT candidate_username FROM votes WHERE user_id = ?", (user_id,))
        check_vote = cursor.fetchone()

        if check_vote:
            conn.close()
            return await message.answer(
                "🚫 <b>Kechirasiz, qoidabuzarlik!</b>\n\nSiz tizimda allaqachon ovoz bergansiz. "
                "Konkurs shaffofligini ta'minlash maqsadida bir foydalanuvchi faqat bitta nomzodga 1 marta ovoz bera oladi.", 
                parse_mode="HTML"
            )

        # Ovozni bazaga yozish
        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes_count = votes_count + 1 WHERE username = ?", (candidate,))
        conn.commit()
        conn.close()
        
        return await message.answer(
            f"✅ <b>Tabriklaymiz!</b>\n\nSiz @{candidate} uchun muvaffaqiyatli ovoz berdingiz. "
            f"Yordamingiz va faolligingiz uchun minnatdormiz!", 
            parse_mode="HTML"
        )

    # ASOSIY START XABARI
    start_text = (
        f"🌟 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        f"Sizni professional tanlovlar va qiziqarli o'yinlar botida ko'rib turganimizdan mamnunmiz. "
        f"Bu yerda siz nafaqat ko'ngilochar o'yinlar o'ynashingiz, balki qimmatbaho sovg'alar "
        f"yutib olishingiz mumkin bo'lgan batllarda qatnashishingiz mumkin.\n\n"
        f"⬇️ <b>Kerakli bo'limni quyidagi menyu orqali tanlang:</b>"
    )
    # Keyboard.py dagi main_menu funksiyasini chaqirish (admin_id ni tekshirgan holda)
    from keyboard import main_menu
    await message.answer(start_text, reply_markup=main_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 2. OVOZLI BATL (KONKURS BOSHLASH) ---
@router.message(F.text == "🎤 Ovozli Batl")
async def battle_starter(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): 
        return

    bot_info = await message.bot.get_me()
    battle_text = (
        "🏆 <b>DIQQAT, KONKURS BOSHLANDI!</b> 🥳\n\n"
        "Aziz kuzatuvchilar, bizning navbatdagi tanlovimizga start berildi! "
        "G'olib bo'lish va o'z kuchingizni ko'rsatish vaqti keldi.\n\n"
        "❕ <b>Asosiy shartlar:</b>\n"
        "1️⃣ Pastdagi tugma orqali ro'yxatdan o'ting.\n"
        "2️⃣ Sizga beriladigan maxsus havola orqali do'stlaringizni chaqiring.\n"
        "3️⃣ Eng ko'p ovoz to'plang va g'oliblikni qo'lga kiriting!\n\n"
        "<blockquote>🚫 <b>Muhim eslatma:</b> Ovoz berish faqat bir marta mumkin. Barcha ovozlar tizim tomonidan qat'iy nazorat qilinadi.</blockquote>\n\n"
        "👇 <b>Ishtirok etish uchun bosing:</b>"
    )
    from keyboard import get_battle_kb
    await message.answer(battle_text, reply_markup=get_battle_kb(bot_info.username), parse_mode="HTML")

# --- 3. NATIJALAR (TOP 5) ---
@router.message(F.text == "📊 Natijalar")
async def results_handler(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): 
        return

    results = get_top_candidates(5)
    if not results:
        return await message.answer("📊 <b>Hozircha faol ishtirokchilar mavjud emas.</b>", parse_mode="HTML")

    msg = "📊 <b>CURRENT TOP 5 RANKING</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, (name, count) in enumerate(results):
        msg += f"<blockquote>{medals[i]} @{name} — <b>{count}</b> ta ovoz</blockquote>\n\n"
    
    await message.answer(msg + "✨ <i>Natijalar real vaqt rejimida yangilanmoqda...</i>", parse_mode="HTML")
