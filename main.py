import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
# XATOLIK BERGAN QATOR OLIB TASHLANDI
# Oldingi xato qator: from handlers import router, update_all_scores
# To'g'risi:
from handlers import router
from database import init_db

# Loglarni yoqamiz
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    init_db()

    # 2. Tokenni olish
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        logging.error("XATO: BOT_TOKEN topilmadi!")
        return

    # Bot ob'ektini yaratish (Xatolik bergan qism olib tashlandi)
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # 3. Routerni ulash
    dp.include_router(router)

    # 4. Tozalash
    await bot.delete_webhook(drop_pending_updates=True)

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
