import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# O'zingning fayllaringdan importlar
from database import get_all_candidates, get_unique_comments_count, init_db
from handlers import router

# --- AVTOMATIK BALL YANGILASH FUNKSIYASI ---
async def auto_update_scores(bot: Bot):
    candidates = get_all_candidates() # Barcha ishtirokchilarni bazadan olish
    for c in candidates:
        # post_id yoki chat_id bo'lmasa tashlab o'tamiz
        if not c.get('post_id') or not c.get('chat_id'): 
            continue
        
        try:
            # 1. Noyob kommentlar sonini olish
            unique_comments = get_unique_comments_count(c['post_id'])
            
            # 2. Reaksiyalar (Kelajakda API ulash uchun joy)
            reactions_count = 0 
            
            # 3. Stars (Yulduzchalar)
            stars_count = 0 

            # --- BALLARNI HISOBLASH ---
            # Reaksiya: har biri +1, max 100
            r_ball = min(reactions_count * 1, 100)
            
            # Komment: har biri +2, max 100
            k_ball = min(unique_comments * 2, 100)
            
            # Stars: har biri +5, cheksiz
            s_ball = stars_count * 5
            
            # Umumiy ball
            total_score = r_ball + k_ball + s_ball

            # --- TAHRIRLASH MATNI ---
            new_text = (
                f"🏆 <b>BATTLE ISHTIROKCHISI:</b> {c['username']}\n\n"
                f"❤️ Reaksiyalar: {reactions_count}/100 (+{r_ball} ball)\n"
                f"💬 Komentlar: {unique_comments}/50 (+{k_ball} ball)\n"
                f"⭐ Stars: {stars_count}/∞ (+{s_ball} ball)\n\n"
                f"📈 <b>UMUMIY BALL: {total_score}</b>"
            )

            # Faqat matn o'zgargan bo'lsagina tahrirlash (Telegram limitiga tushmaslik uchun)
            # Bu yerda oddiy tahrirlash:
            await bot.edit_message_text(
                chat_id=c['chat_id'],
                message_id=c['post_id'],
                text=new_text,
                parse_mode="HTML"
            )
            
        except Exception as e:
            # Xabarni tahrirlab bo'lmasa (masalan, o'chirilgan bo'lsa) log yozadi
            logging.error(f"Update xatosi ({c['username']}): {e}")

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    init_db()

    # 2. Tokenni olish (os.getenv ishlamasa, qo'shtirnoq ichiga tokenni yozib qo'y)
    TOKEN = os.getenv("BOT_TOKEN") or "BU_YERGA_TOKEN_YOKI_ENV_ISHLATING"
    
    if not TOKEN or TOKEN == "BU_YERGA_TOKEN_YOKI_ENV_ISHLATING":
        logging.error("XATO: BOT_TOKEN topilmadi!")
        return

    # Bot ob'ekti (Aiogram 3.x uchun to'g'ri format)
    bot = Bot(
        token=TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 3. Routerni ulash
    dp.include_router(router)

    # --- 4. SCHEDULERNI SOZLASH (ASOSIY QISM) ---
    scheduler = AsyncIOScheduler()
    # Har 2 daqiqada ballarni yangilab turadi
    scheduler.add_job(auto_update_scores, "interval", minutes=2, args=[bot])
    scheduler.start()

    # 5. Keraksiz xabarlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    # 6. Pollingni boshlash
    logging.info("Bot muvaffaqiyatli ishga tushdi!")
    try:
        await dp.start_polling(
            bot, 
            allowed_updates=["message", "callback_query", "channel_post", "inline_query"]
        )
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")
