import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import setup_database
from keyboards import main_menu_keyboard
from handlers import register_handlers
from handlers import register_handlers


# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

if __name__ == "__main__":
    # Настройка базы данных
    setup_database()

    # Регистрация обработчиков
    register_handlers(dp)

    # Запуск бота
    executor.start_polling(dp, skip_updates=True)