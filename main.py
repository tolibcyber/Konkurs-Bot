import asyncio
import logging
import os  # Muhit o'zgaruvchilari (token) uchun kerak
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from handlers import router, auto_update_scores # auto_update_scores qo'shildi
asyncio.create_task(auto_update_scores(Bot))
from database import init_db

# Loglarni yoqamiz (Xato bo'lsa terminalda ko'rinadi)
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    init_db()

    # 2. Tokenni Render sozlamalaridan olish
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        logging.error("XATO: BOT_TOKEN topilmadi! Render sozlamalarini tekshiring.")
        return

    # Bot va Dispatcher ob'ektlarini yaratish
    # Default parse_mode ni HTML qilib qo'yamiz, shunda hamma joyda ishlidi
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # 3. Routerni ulash
    dp.include_router(router)

    # --- YANGI QISM: 5 MINUTLIK MOTORNI ISHGA TUSHIRISH ---
    # Bu qator bot polling boshlanishi bilan fonda ballarni yangilashni boshlaydi
    asyncio.create_task(auto_update_scores(bot))
    # ---------------------------------------------------

    # 4. Tozalash (Bot o'chiq turganda kelgan xabarlarni o'chirib yuboradi)
    await bot.delete_webhook(drop_pending_updates=True)

    # 5. Pollingni boshlash
    await dp.start_polling(
        bot, 
        allowed_updates=["message", "callback_query", "channel_post", "inline_query"]
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")
