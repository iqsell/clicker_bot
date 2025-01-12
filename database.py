import sqlite3

def setup_database():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Создаем таблицу пользователей с новым столбцом для отслеживания бонуса
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,                  -- Уникальный идентификатор пользователя
        username TEXT,                            -- Имя пользователя
        balance_egp INTEGER DEFAULT 0,            -- Баланс в EGP
        miner_level INTEGER DEFAULT 1,            -- Уровень майнера
        clicks_today INTEGER DEFAULT 0,           -- Количество кликов сегодня
        total_clicks INTEGER DEFAULT 0,           -- Общее количество кликов
        total_referrals INTEGER DEFAULT 0,        -- Общее количество рефералов
        progress INTEGER DEFAULT 0,               -- Прогресс
        balance_hash INTEGER DEFAULT 0,           -- Баланс хэша
        bonus_received INTEGER DEFAULT 0          -- Столбец для отслеживания бонуса (0 - не получен, 1 - получен)
    )''')

    # Создаем таблицу для рефералов (если необходимо)
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        referral_user_id INTEGER,
        referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')

    # Создаем таблицу для записей о транзакциях (например, для бонусов и выводов)
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        transaction_type TEXT,           -- Тип транзакции: 'bonus', 'deposit', 'withdrawal'
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')

    conn.commit()
    conn.close()
