import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db
from flask import Flask
from threading import Thread

# Render uchun kichik web-server (o'chib qolmasligi uchun port ochadi)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render aynan 10000-portni kutadi
    app.run(host='0.0.0.0', port=10000)

async def main():
    # Tokenni Render-dagi Environment Variables-dan oladi
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        logging.error("XATOLIK: BOT_TOKEN topilmadi! Render-da Environment Variables bo'limiga tokenni qo'shing.")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Handlerlarni ulash
    dp.include_router(router)
    
    # Ma'lumotlar bazasini ishga tushirish
    init_db()
    
    # Loglarni sozlash
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Web-serverni alohida potokda yoqish (Render "No open ports" demasligi uchun)
    Thread(target=run_flask, daemon=True).start()
    
    # Eskidan qolib ketgan xabarlarni o'chirib yuborish
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Botni ishga tushirish
    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")