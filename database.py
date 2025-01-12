import sqlite3

def setup_database():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Создаем таблицу пользователей с новым столбцом для отслеживания бонуса
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        balance_egp INTEGER DEFAULT 0,  -- Добавляем столбец для EGP баланса
        miner_level INTEGER DEFAULT 1,
        clicks_today INTEGER DEFAULT 0,
        total_clicks INTEGER DEFAULT 0,
        total_referrals INTEGER DEFAULT 0,
        progress INTEGER DEFAULT 0,  -- Добавляем столбец для прогресса
        balance_hash INTEGER DEFAULT 0,  -- Добавляем столбец для баланса хэша
        bonus_received INTEGER DEFAULT 0  -- Новый столбец для отслеживания бонуса
    )''')

    conn.commit()
    conn.close()
