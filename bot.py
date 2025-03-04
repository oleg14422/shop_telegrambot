import asyncio
import os
import dotenv
from utils import bot_logger
from admin_handlers import admin_router
from user_handlers import user_router
from aiogram import  Dispatcher, Bot
from db import init_db


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)
    bot_logger.info('env loaded')
else:
    bot_logger.critical('Could not find .env file.')

TOKEN = os.getenv('TOKEN')
dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(user_router)
bot = Bot(TOKEN)



async def main():
    bot_logger.info('Bot started')
    await init_db()
    bot_logger.info('Database initialized')
    await dp.start_polling(bot)

asyncio.run(main())