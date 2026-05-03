import sqlite3
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from keyboard import main_menu, get_battle_kb, sub_keyboard
from database import ADMIN_ID, get_top_candidates, add_user

router = Router()

# --- 1. START XABARI VA OVOZ BERISH ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username) # Foydalanuvchini bazaga qo'shish
    
    # REFERAL LINK ORQALI KELGANDA OVOZ BERISHNI TEKSHIRISH
    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # FOYDALANUVCHI OLDIN OVOZ BERGANMI? (UNIQUIE CHECK)
        cursor.execute("SELECT candidate_username FROM votes WHERE user_id = ?", (user_id,))
        already_voted = cursor.fetchone()

        if already_voted:
            conn.close()
            return await message.answer(
                "🚫 <b>Kechirasiz, qoidabuzarlik!</b>\n\n"
                "Siz tizimda allaqachon ovoz bergansiz. Konkurs shaffofligini ta'minlash maqsadida "
                "har bir foydalanuvchi faqat <b>1 marta</b> va faqat <b>1 ta</b> nomzodga ovoz bera oladi. "
                "Adolatli o'yin tarafdori bo'lganingiz uchun rahmat! 😊", 
                parse_mode="HTML"
            )

        # OVOZNI QABUL QILISH VA BAZANI YANGILASH
        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes_count = votes_count + 1 WHERE username = ?", (candidate,))
        conn.commit()
        conn.close()
        
        return await message.answer(
            f"✅ <b>Rahmat! Ovoz muvaffaqiyatli qabul qilindi.</b>\n\n"
            f"Siz @{candidate} ishtirokchisi uchun ovoz berdingiz. Sizning tanlovingiz "
            f"g'olibni aniqlashda katta ahamiyatga ega! 🔥", 
            parse_mode="HTML"
        )

    # ASOSIY START XABARI (CHIROYLI VA TUSHUNARLI)
    start_txt = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        f"Sizni botimizda ko'rib turganimizdan juda xursandmiz! Bu yerda siz quyidagi imkoniyatlarga egasiz:\n\n"
        f"🎡 <b>Baraban:</b> O'z omadingizni sinab ko'ring va ajoyib sovg'alar yuting!\n"
        f"✌️ <b>Enik-Benik:</b> Do'stlaringiz bilan qiziqarli o'yinlar o'ynab, vaqtingizni mazmunli o'tkazing!\n"
        f"🎤 <b>Ovozli Batl:</b> O'z kanalingizda professional konkurslar tashkil qiling va g'oliblarni aniqlang!\n\n"
        f"🚀 <b>Pastdagi menyudan o'zingizga kerakli bo'limni tanlang:</b>"
    )
    
    await message.answer(
        start_txt, 
        reply_markup=main_menu(user_id, ADMIN_ID), 
        parse_mode="HTML"
    )

# --- 2. KONKURS BOSHLASH (OVOZLI BATL TUGMASI) ---
@router.message(F.text == "🎤 Ovozli Batl")
async def battle_starter(message: types.Message):
    # Faqat admin uchun ruxsat
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
        "<blockquote>🚫 <b>Eslatma:</b> Bir foydalanuvchi faqat 1 marta ovoz bera oladi. Barcha jarayonlar bot tomonidan qat'iy nazorat qilinadi.</blockquote>\n\n"
        "👇 <b>Tanlovda qatnashish uchun bosing:</b>"
    )
    await message.answer(battle_text, reply_markup=get_battle_kb(bot_info.username), parse_mode="HTML")

# --- 3. KONKURSGA QO'SHILISH (CALLBACK) ---
@router.callback_query(F.data == "join_contest")
async def join_callback(callback: types.CallbackQuery):
    user_username = callback.from_user.username
    if not user_username:
        return await callback.answer("❌ Xatolik: Profilingizda 'username' o'rnatilmagan! Iltimos, sozlamalardan username qo'shing.", show_alert=True)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username) VALUES (?)", (user_username,))
        conn.commit()
        
        bot_info = await callback.bot.get_me()
        share_url = f"https://t.me/{bot_info.username}?start=vote_{user_username}"
        
        await callback.message.answer(
            f"🎉 <b>Tabriklaymiz, siz ro'yxatdasiz!</b>\n\n"
            f"Sizning shaxsiy tanlov havolangiz:\n<code>{share_url}</code>\n\n"
            f"Ushbu havolani do'stlaringizga yuboring va ovoz to'plashni boshlang! Omad yor bo'lsin! 🔥",
            parse_mode="HTML"
        )
    except sqlite3.IntegrityError:
        await callback.answer("😊 Siz allaqachon ishtirokchilar orasida mavjudsiz.", show_alert=True)
    finally:
        conn.close()

# --- 4. NATIJALAR (TOP 5) ---
@router.message(F.text == "📊 Natijalar")
async def results_handler(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): 
        return

    results = get_top_candidates(5)
    if not results:
        return await message.answer("📊 <b>Hozircha faol ishtirokchilar va ovozlar mavjud emas.</b>", parse_mode="HTML")

    msg = "📊 <b>CURRENT TOP 5 RANKING</b>\n🏆 <b>Eng kuchli nomzodlar ro'yxati:</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, (name, count) in enumerate(results):
        msg += f"<blockquote>{medals[i]} @{name} — <b>{count}</b> ta ovoz</blockquote>\n\n"
    
    await message.answer(msg + "✨ <i>Natijalar har bir ovozdan so'ng real vaqtda yangilanadi.</i>", parse_mode="HTML")
