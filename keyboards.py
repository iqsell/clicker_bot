from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


# Основное меню
def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Зарабатывать"))
    keyboard.add(KeyboardButton("Заработать больше"), KeyboardButton("Топ пользователей"))
    keyboard.add(KeyboardButton("Рефералка"), KeyboardButton("Профиль"))
    keyboard.add(KeyboardButton("Обмен Coins"), KeyboardButton("Выплаты"))
    keyboard.add(KeyboardButton("FAQ"))
    keyboard.add(KeyboardButton("Промокод"))
    return keyboard

# Меню для заработка
def earn_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Click"))
    keyboard.add(KeyboardButton("Повысить уровень майнера"))
    keyboard.add(KeyboardButton("Вернуться в меню"))
    return keyboard

# Инлайн кнопка "Click"
def click_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Click", callback_data="click"))
    return keyboard

# Кнопка для подтверждения подписки и получения бонуса
def earn_more_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    # Кнопка "Канал" — перенаправление на канал
    keyboard.add(InlineKeyboardButton("Канал", url="https://t.me/testingtesting131"))

    # Кнопка для проверки подписки и получения бонуса
    keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="check_subscription"))
    return keyboard

# Кнопка для возврата в меню
def back_to_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Вернуться в главное меню"))
    return keyboard

def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Отмена"))
    return keyboard

def withdrawals_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("AMERIKA FINANCIERA S.A."), KeyboardButton("BANCO AZTECA DEL PERU, S.A."))
    keyboard.add(KeyboardButton("BANCO CENTRAL DE RESERVA DEL PERU"), KeyboardButton("BANCO CONTINENTAL"))
    keyboard.add(KeyboardButton("TRC-20"))
    keyboard.add(KeyboardButton("Вернуться в меню"))
    return keyboard

