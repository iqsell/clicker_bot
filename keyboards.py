from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


# Основное меню
def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🍬Earn"))
    keyboard.add(KeyboardButton("🥂Earn more"), KeyboardButton("🏆Users Top"))
    keyboard.add(KeyboardButton("🎰Referral"), KeyboardButton("🗿Profile"))
    keyboard.add(KeyboardButton("💸Coin Exchange"), KeyboardButton("💰payout"))
    keyboard.add(KeyboardButton("💎FAQ"))
    keyboard.add(KeyboardButton("✈️Additionally"))
    return keyboard

# Меню для заработка
def earn_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⛏️Click"))
    keyboard.add(KeyboardButton("⬆️lead the miner's node"))
    keyboard.add(KeyboardButton("🔙Return to menu"))
    return keyboard

# Инлайн кнопка "Click"
def click_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⛏️Click", callback_data="⛏️click"))
    return keyboard

# Кнопка для подтверждения подписки и получения бонуса
def earn_more_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    # Кнопка "Канал" — перенаправление на канал
    keyboard.add(InlineKeyboardButton("📰Channel", url="https://t.me/testingtesting131"))

    # Кнопка для проверки подписки и получения бонуса
    keyboard.add(InlineKeyboardButton("✅Accept", callback_data="check_subscription"))
    return keyboard

def earn_more_keyboard():
    keyboard = InlineKeyboardMarkup()
    # Кнопка "Канал" — перенаправление на канал
    keyboard.add(InlineKeyboardButton("Channel", url="https://t.me/testingtesting131"))
    return keyboard

# Кнопка для возврата в меню
def back_to_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Go back to the main menu"))
    return keyboard

def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("cancellation"))
    return keyboard

def withdrawals_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("AMERIKA FINANCIERA S.A."), KeyboardButton("BANCO AZTECA DEL PERU, S.A."))
    keyboard.add(KeyboardButton("BANCO CENTRAL DE RESERVA DEL PERU"), KeyboardButton("BANCO CONTINENTAL"))
    keyboard.add(KeyboardButton("TRC-20"))
    keyboard.add(KeyboardButton("🔙Return to menu"))
    return keyboard

