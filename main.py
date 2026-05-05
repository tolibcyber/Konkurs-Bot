import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultKeyboardOptions
from aiogram.enums import ParseMode
from handlers import router, update_all_scores  # Ovozlar yangilanishi uchun
from database import init_db

# Loglarni yoqamiz
logging.basicConfig(level=logging.INFO)

async def auto_update_scores_loop(bot: Bot):
    """
    Har 30 soniyada kanaldagi ovozlar sonini tekshirib, 
    o'zgargan bo'lsa postni yangilab turadi.
    """
    while True:
        try:
            await update_all_scores(bot)
            await asyncio.sleep(30) # 30 soniya kutish (yuklamani kamaytirish uchun)
        except Exception as e:
            logging.error(f"Yangilashda xatolik: {e}")
            await asyncio.sleep(10)

async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    init_db()

    # 2. Tokenni olish (Railway yoki boshqa hostda BOT_TOKEN nomida bo'lishi shart)
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        logging.error("XATO: BOT_TOKEN topilmadi! Railway 'Variables' qismini tekshiring.")
        return

    # Bot va Dispatcher ob'ektlarini yaratish
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # 3. Routerni ulash
    dp.include_router(router)

    # 4. Tozalash (Bot o'chiq turganda kelgan xabarlarni o'tkazib yuborish)
    await bot.delete_webhook(drop_pending_updates=True)

    # 5. Ovozlar yangilanishi uchun fon vazifasini ishga tushirish (Motor)
    # Bu qism faqat ishtirokchilar ovozini kanalda yangilab turish uchun kerak
    asyncio.create_task(auto_update_scores_loop(bot))

    # 6. Pollingni boshlash
    logging.info("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(
        bot, 
        allowed_updates=["message", "callback_query", "channel_post", "inline_query"]
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")
