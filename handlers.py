import sqlite3
import asyncio
import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

# Klaviaturalar va baza funksiyalarini sening fayllaringdan import qilamiz
from keyboard import (
    main_reply_menu, admin_menu_kb, voice_battle_kb, 
    get_battle_kb, sub_keyboard, section_inline_kb, 
    enik_benik_inline_kb, back_to_main_kb
)
from database import (
    add_user, ADMIN_ID, get_total_users, get_all_user_ids,
    update_candidate_post_id
)

router = Router()
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}
REQUIRED_CHANNEL = "@TolibTokyo"

class AdminStates(StatesGroup):
    waiting_for_ad = State()
    waiting_for_battle_text = State()
    waiting_for_battle_channel = State()

# --- 1. BAZA BILAN ISHLASH (NOMZODLAR) ---
def add_candidate_to_db(username, chat_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM candidates WHERE username = ? AND chat_id = ?", (username, str(chat_id)))
        if cursor.fetchone(): return False
        cursor.execute("INSERT INTO candidates (username, votes, chat_id) VALUES (?, ?, ?)", (username, 0, str(chat_id)))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Baza xatosi: {e}")
        return False
    finally:
        conn.close()

def get_all_candidates():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes, chat_id FROM candidates ORDER BY votes DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- 2. YORDAMCHI FUNKSIYALAR ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

async def check_user_is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["administrator", "creator"] or str(user_id) == str(ADMIN_ID)
    except: return False

# --- 3. START HANDLER (6 TA TUGMA BILAN) ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username) 

    # Ovoz berish mantiqi (Deep Link)
    args = command.args
    if args and args.startswith("vote_"):
        if not await is_subscribed(message.bot, user_id):
            return await message.answer("⚠️ Ovoz berish uchun avval kanalga a'zo bo'ling!", 
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
        
        # Kanalda postni yangilash
        if LAST_BATTLE_POST["message_id"]:
            all_c = get_all_candidates()
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=LAST_BATTLE_POST["chat_id"],
                    message_id=LAST_BATTLE_POST["message_id"],
                    reply_markup=get_battle_kb(all_c, (await message.bot.get_me()).username)
                )
            except: pass
        return

    # Asosiy Menyu (6 ta knopka)
    start_txt = (
        f"👋 Salom <b>{message.from_user.first_name}</b>!\n\n"
        f"Sizni botimizda ko'rib turganimizdan xursandmiz! Bu yerda quyidagi imkoniyatlar mavjud:\n\n"
        f"🎡 <b>Baraban:</b> Ism yozib g'olibni aniqlang!\n"
        f"✌️ <b>Enik-Benik:</b> Qiziqarli mini o'yinlar!\n"
        f"🎤 <b>Ovozli Batl:</b> Kanallar uchun professional konkurslar!\n"
        f"🚀 <b>Tekin Nakrutka:</b> Kanalingizni bepul rivojlantiring!\n"
        f"🛠 <b>Xizmatlar:</b> Bizning boshqa botlar va xizmatlar!\n\n"
        f"👇 Kerakli bo'limni tanlang:"
    )
    await message.answer(start_txt, reply_markup=main_reply_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- 4. ASOSIY MENYU TUGMALARI ISHLASHI ---

@router.message(F.text == "🎡 Baraban o'yini")
async def baraban_btn(message: types.Message):
    await message.answer("🎡 <b>Baraban o'yini</b> bo'limi!\nOmadingizni sinab ko'ring:", 
                         reply_markup=section_inline_kb(url="https://games-new2.netlify.app/"), parse_mode="HTML")

@router.message(F.text == "✌️ Enik-Benik")
async def enik_benik_btn(message: types.Message):
    await message.answer("✌️ <b>Enik-Benik</b> o'yiniga xush kelibsiz!\nO'yinni boshlash uchun:", 
                         reply_markup=enik_benik_inline_kb(url="https://games-new1.netlify.app/"), parse_mode="HTML")

@router.message(F.text == "🎤 Ovozli Batl")
async def voice_battle_btn(message: types.Message):
    bot_info = await message.bot.get_me()
    guide = (
        "🎤 <b>Ovozli Batl Tashkil Qilish</b>\n\n"
        "1. Botni kanalingizga qo'shib admin qiling.\n"
        "2. Kanalga <code>#konkursx</code> deb yozing.\n"
        "3. Bot avtomatik konkurs postini yaratadi.\n"
        "💎 Har bir ovoz beruvchi kanalingizga a'zo bo'ladi!"
    )
    await message.answer(guide, reply_markup=voice_battle_kb(bot_info.username), parse_mode="HTML")

@router.message(F.text == "🚀 Tekin Nakrutka")
async def free_boost_btn(message: types.Message):
    await message.answer("<b>🚀 Tekin Nakrutka bo'limi!</b>\n\n"
        "Do'stlar, bu bo'lim hali tayyorlanmoqda. Botimiz foydalanuvchilari soni "
        "<b>1000 taga</b> yetishi bilan ushbu xizmat mutlaqo tekin ishga tushadi! 😍\n\n"
        "Hozirda foydalanuvchilarimiz ozroq botda. Botni do'stlaringizga ulashing va "
        "imkoniyatni tezroq oching! ✨")

@router.message(F.text == "🛠 Xizmatlar / Qollab-quvvatlash")
async def support_btn(message: types.Message):
    await message.answer("<b>🛠 Bizning Xizmatlar:</b>\n"
        "• Bot yaratish xizmati\n"
        "• Kanallarni reklama qilish\n"
        "• Texnik yordam\n\n"
        "Savollaringiz bo'lsa, adminga murojaat qiling: @TolibDev",
         
     parse_mode="HTML")

# --- 5. KONKURS BOSHLASH (#konkursx) ---
@router.channel_post(F.text.contains("#konkursx"))
@router.message(F.text.contains("#konkursx"))
async def start_contest(message: types.Message):
    if message.chat.type not in ["channel", "group", "supergroup"]: return
    try: await message.delete() 
    except: pass

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates"); cursor.execute("DELETE FROM votes")
    conn.commit(); conn.close()

    battle_text = (
        f"📣 <b>{message.chat.title} | YANGI BATL!</b>\n\n"
        f"Ishtirok eting va do'stlaringizdan ovoz yig'ing! ✅\n\n"
        f"⚠️ <b>Shart:</b> Faqat kanal a'zolarining ovozi hisoblanadi!\n\n"
        f"🎁 Yutuq: <tg-spoiler>Sirli sovg'a! 🤫</tg-spoiler>"
    )
    bot_me = await message.bot.get_me()
    msg = await message.answer(battle_text, reply_markup=get_battle_kb([], bot_me.username), parse_mode="HTML")
    LAST_BATTLE_POST["chat_id"] = message.chat.id
    LAST_BATTLE_POST["message_id"] = msg.message_id

# --- 6. CALLBACKLAR (QATNASHISH VA NATIJALAR) ---

@router.callback_query(F.data == "join_contest")
async def join_handler(callback: types.CallbackQuery):
    user = callback.from_user
    if not user.username:
        return await callback.answer("⚠️ Avval username o'rnating!", show_alert=True)
    
    if add_candidate_to_db(f"@{user.username}", callback.message.chat.id):
        all_c = get_all_candidates()
        await callback.message.edit_reply_markup(reply_markup=get_battle_kb(all_c, (await callback.bot.get_me()).username))
        await callback.answer("✅ Ro'yxatga qo'shildingiz!", show_alert=True)
    else:
        await callback.answer("🚫 Siz allaqachon ro'yxatdasiz!", show_alert=True)

# --- 5. NATIJALAR (FAQAT ADMINLAR) ---
@router.callback_query(F.data == "results")
async def results_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # Adminlikni tekshirish
    is_admin = await check_user_is_admin(callback.bot, chat_id, user_id)

    if not is_admin:
        return await callback.answer(
            "⚠️ Kechirasiz, natijalarni faqat kanal adminlari e'lon qilishi mumkin!", 
            show_alert=True
        )

    candidates = get_all_candidates()
    if not candidates:
        return await callback.answer("Hozircha nomzodlar yo'q!", show_alert=True)

    top_5 = candidates[:5]
    top_txt = (
        "📊 <b>JORIY NATIJALAR | TOP 5</b>\n\n"
        "───────────────────\n"
    )
    for i, c in enumerate(top_5, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}️⃣")
        top_txt += f"{medal} <b>{c['username']}</b> — <code>{c['votes']}</code> ta ovoz\n"
    
    top_txt += (
        "───────────────────\n\n"
        "🏆 <b>G'oliblik sari intiling!</b>\n"
        "📢 <i>Do'stlaringizni taklif qilishda davom eting.</i>"
    )

    await callback.message.answer(top_txt, parse_mode="HTML")
    await callback.answer("Natijalar muvaffaqiyatli e'lon qilindi! ✅")

# --- 7. ADMIN PANEL ---

@router.message(F.text == "⚙️ Admin Panel")
async def admin_panel_btn(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    await message.answer("<b>⚙️ Admin Paneliga xush kelibsiz!</b>", reply_markup=admin_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data == "admin_stats")
async def stats_callback(callback: types.CallbackQuery):
    total = get_total_users()
    await callback.message.edit_text(f"📊 <b>Statistika:</b>\n\nFoydalanuvchilar: {total} ta", 
                                     reply_markup=back_to_main_kb(), parse_mode="HTML")

@router.callback_query(F.data == "send_ads")
async def ads_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Reklama xabarini yuboring yoki /cancel bosing:")
    await state.set_state(AdminStates.waiting_for_ad)

@router.message(AdminStates.waiting_for_ad)
async def process_ads(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear(); return await message.answer("Bekor qilindi.")
    
    uids = get_all_user_ids()
    count = 0
    for uid in uids:
        try:
            await message.copy_to(chat_id=uid[0])
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    
    await message.answer(f"✅ Reklama {count} kishiga yuborildi!")
    await state.clear()
