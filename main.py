import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from handlers import router
from database import create_db

# Bot tokeningni shu yerga yoz yoki Environment-dan olsin
TOKEN = "TOKENINGNI_SHU_YERGA_YOZ"

async def main():
    # 1. Bazani yaratish (Agar bo'lmasa)
    create_db()
    
    # 2. Bot va Dispatcher ob'ektlarini yaratish
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # 3. Loglarni sozlash
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # 4. Conflict-ni oldini olish: Eski webhook yoki sessiyalarni o'chirish
    # Bu aynan logdagi "Conflict: terminated by other getUpdates" xatosini yechadi
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 Bot muvaffaqiyatli ishga tushdi...")
    
    # 5. Botni yurgizish (Polling)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")
