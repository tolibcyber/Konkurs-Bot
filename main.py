import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from handlers import router
from database import init_db

# Loglarni yoqamiz (Xato bo'lsa terminalda ko'rinadi)
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    init_db()

    # 2. Bot va Dispatcher ob'ektlarini yaratish
    # Tokeningizni shu yerda qoldirdim, o'zgartirmang
    bot = Bot(token="8139457013:AAHuRtJzTg_1qXR1r7e8o6KUY9SB6IrLZNM")
    dp = Dispatcher()

    # 3. Routerni ulash
    dp.include_router(router)

    # 4. Tozalash (Bot o'chiq turganda kelgan xabarlarni o'chirib yuboradi)
    await bot.delete_webhook(drop_pending_updates=True)

    # 5. Pollingni boshlash (MUHIM: allowed_updates qo'shildi!)
    # Bu botga ham guruhlar, ham kanallardagi postlarni o'qishga ruxsat beradi
    await dp.start_polling(
        bot, 
        allowed_updates=["message", "callback_query", "channel_post", "inline_query"]
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")