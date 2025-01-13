import sqlite3
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from keyboards import earn_menu_keyboard, earn_more_keyboard, cancel_keyboard, withdrawals_keyboard, \
    click_inline_keyboard, main_menu_keyboard, earn_more_inline_keyboard
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command


class ExchangeCoins(StatesGroup):
    waiting_for_amount = State()  # Состояние для ввода суммы


class Withdrawall(StatesGroup):
    waiting_for_amount = State()  # Состояние для ввода суммы


async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    args = message.get_args()  # Получаем аргументы команды /start

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Проверяем, существует ли пользователь
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # Добавляем нового пользователя
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()

        # Проверяем, есть ли реферальный код
        if args.startswith("ref_"):
            try:
                referrer_id = int(args.split("_")[1])

                # Проверяем, что пригласивший пользователь существует
                cursor.execute("SELECT user_id FROM users WHERE user_id=?", (referrer_id,))
                referrer = cursor.fetchone()

                if referrer:
                    # Добавляем запись в таблицу referrals
                    cursor.execute(
                        "INSERT INTO referrals (user_id, referral_user_id) VALUES (?, ?)",
                        (referrer_id, user_id)
                    )

                    # Увеличиваем счетчик total_referrals для пригласившего
                    cursor.execute(
                        "UPDATE users SET total_referrals = total_referrals + 1 WHERE user_id=?",
                        (referrer_id,)
                    )

                    # Начисляем бонус пригласившему
                    cursor.execute(
                        "UPDATE users SET balance_egp = balance_egp + 60 WHERE user_id=?",
                        (referrer_id,)
                    )

                    # (Опционально) Начисляем бонус новому пользователю
                    cursor.execute(
                        "UPDATE users SET balance_egp = balance_egp + 60 WHERE user_id=?",
                        (user_id,)
                    )

                    conn.commit()

            except (ValueError, IndexError):
                # Неверный формат реферального кода
                pass

    conn.close()

    await message.answer(
        "Welcome! You have successfully registered.",
        reply_markup=main_menu_keyboard()
    )


# Обработчик для кнопки "Зарабатывать"
async def earn_handler(message: Message):
    await message.answer("Select an action:", reply_markup=earn_menu_keyboard())  # Меню с обычными кнопками


# Обработчик для нажатия на кнопку "Click" в обычном меню
async def click_menu_handler(message: Message):
    await message.answer("You have started the click process! Click on the button below:",
                         reply_markup=click_inline_keyboard())


async def click_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Получаем данные о пользователе из базы
    cursor.execute("""
        SELECT clicks_today, progress, miner_level, balance_hash 
        FROM users 
        WHERE user_id=?
    """, (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        clicks_today, progress, miner_level, balance_hash = user_data

        # Проверка, если лимит в 100 кликов уже достигнут
        if clicks_today >= 100:
            # Отправляем сообщение о завершении задания
            await callback_query.message.edit_text(
                "You have completed 100 out of 100 possible tasks.\n"
                "New missions will appear within 24 hours.\n"
                "You can earn a lot more money on this channel.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Earn money", url="https://t.me/your_channel_link")
                )
            )
            # Отправляем ответ на клик
            await callback_query.answer("You have reached the click limit for today.")
        else:
            # Увеличиваем количество кликов
            clicks_today += 1

            # Расчитываем прогресс
            progress = int((clicks_today / 100) * 100)  # Прогресс в процентах
            if progress > 100:
                progress = 100  # Прогресс не должен превышать 100%

            # Определяем монеты за клик в зависимости от уровня
            coins_per_click = 100 * miner_level  # Количество монет зависит от уровня

            # Добавляем монеты в баланс хэша
            balance_hash += coins_per_click

            # Обновляем данные в базе данных
            cursor.execute("""
                UPDATE users 
                SET clicks_today = ?, progress = ?, balance_hash = ? 
                WHERE user_id = ?
            """, (clicks_today, progress, balance_hash, user_id))
            conn.commit()

            # Формируем сообщение с актуальной информацией
            message_text = (
                f"📅 Today: {clicks_today} / 100\n"
                f"📈 Progress: {progress}%\n"
                f"🪙 Coin click: {coins_per_click}\n"
                f"⛏️ Mining level: {miner_level}\n"
                f"💎 Balance: {balance_hash}")
            # Попробуем обновить сообщение с информацией
            try:
                await callback_query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("⛏️Click", callback_data="⛏️click")
                    )
                )
            except Exception as e:
                print(f"Error editing the message: {e}")

            # Отправляем ответ на клик
            await callback_query.answer("You have clicked on the Click button!")

    else:
        # Если пользователь не найден, уведомляем об этом
        await callback_query.answer("The user was not found. Please register.")

    conn.close()


async def process_exchange(message: Message, state: FSMContext):
    user_id = message.from_user.id
    amount = message.text

    try:
        amount = int(amount)
    except ValueError:
        await message.answer("Please enter the correct number.")
        return

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance_hash FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        balance_hash = user_data[0]
        max_egp = balance_hash // 200  # Курс обмена

        if amount <= 0:
            await message.answer("The amount exchanged cannot be negative or zero.")
        elif amount > max_egp:
            await message.answer(f"You can exchange no more than {max_egp} EGP.")
        else:
            coins_to_exchange = amount * 200  # 1 EGP = 200 coins
            new_balance_hash = balance_hash - coins_to_exchange

            # Обновляем балансы
            cursor.execute("UPDATE users SET balance_hash=? WHERE user_id=?", (new_balance_hash, user_id))
            cursor.execute("SELECT balance_egp FROM users WHERE user_id=?", (user_id,))
            user_data_egp = cursor.fetchone()
            if user_data_egp:
                balance_egp = user_data_egp[0] + amount
                cursor.execute("UPDATE users SET balance_egp=? WHERE user_id=?", (balance_egp, user_id))
                conn.commit()

                await message.answer(
                    f"Successfully exchanged {amount} EGP\n"
                    f"Your new balance: {balance_egp} EGP"
                )
            else:
                await message.answer("An error occurred when updating your balance.")
        await state.finish()  # Завершаем состояние
    conn.close()


async def cancel_handler(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await message.answer("You are back in the main menu.", reply_markup=main_menu_keyboard())


# Обработчик для повышения уровня
async def level_up_handler(message: Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT miner_level, balance_hash FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        miner_level, balance_hash = user_data

        # Стоимость улучшения уровней
        upgrade_costs = [80000, 160000]  # Стоимость для 2-го и 3-го уровней
        next_level_cost = None
        if miner_level < 3:
            next_level_cost = upgrade_costs[miner_level - 1] if miner_level > 0 else upgrade_costs[0]

            if balance_hash >= next_level_cost:
                # Повышаем уровень майнера
                miner_level += 1
                balance_hash -= next_level_cost

                # Обновляем в базе данных
                cursor.execute("UPDATE users SET miner_level=?, balance_hash=? WHERE user_id=?",
                               (miner_level, balance_hash, user_id))
                conn.commit()

                # Отправляем сообщение о повышении уровня
                await message.answer(
                    f"Congratulations! Your miner level has increased to {miner_level}. "
                    f"Now you get 2 times more hash per click.",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Raise the miner's level", callback_data="level_up")
                    )
                )
            else:
                # Если недостаточно средств для улучшения
                await message.answer(
                    f"You don't have enough {next_level_cost - balance_hash} coins to level up. "
                    f"Required amount for improvement: {next_level_cost}.",
                )
        else:
            # Если достигнут максимальный уровень
            await message.answer(
                "You have the maximum miner level. Further improvements are not provided."
            )
    conn.close()


# Обработчик для возвращения в меню
async def back_to_menu_handler(message: Message):
    await message.answer("You are back in the main menu.", reply_markup=main_menu_keyboard())


# Обработчик для кнопки "FAQ"
async def faq_handler(message: Message):
    # Формируем сообщение с FAQ
    faq_text = (
        "What kind of bot is this?\n"
        "- With this Telegram bot, you can earn money by clicking the 'Click' button.\n\n"

        "How does it work?\n"
        " is pretty simple. Each of your clicks gets a certain amount of power on our servers, "
        "which allows you to mine cryptocurrency in the shortest possible time.\n\n"

        "How do I start earning?\n"
        " Is easy! Click the 'Mining' button, and then click the 'Click' button.\n"
        "- For each click you will receive a certain number of coins, which in the future will allow you to "
        "convert coins to bitcoins, and then exchange bitcoins for EGP and withdraw money.\n\n"

        "I have a certain amount of coins, what's next?\n"
        "- Then you need to click the 'Exchange coins' button and exchange coins for Bitcoin.\n\n"

        "How to exchange bitcoins for EGP? How to withdraw money?\n"
        "- To withdraw money, you need to go to the main menu and click the 'Withdraw funds' button. "
        "Then choose any convenient way for you to receive your money.\n"
        "- !!! Remember that withdrawal is available from level 3!!!\n\n"

        "How to level up and why?\n"
        "- Each level allows you to get more coins per click. For example, at the first level you get 25 coins per click, "
        "at the second level - 60 coins. Also, you need level 3 to withdraw money.\n"
        "- To level up, you must have a certain number of coins. For example, to advance to the second level, "
        "you need to have 12,500 coins. If you have this amount of coins, go to the 'Mining' menu and click the"
        "'Improve Miner level' button, and then the 'Upgrade' button.\n\n"

        "How to earn more?\n"
        "- To earn more, we have introduced a referral system and tasks from sponsors.\n\n"

        "How to make money in the referral system?\n"
        "- To do this, you will receive a personal link 'Money to a friend' in the menu. Take this link and send it to your friends "
        "or post it in various sources: for example, on Facebook or Tik-Tok.\n"
        "- There are also levels in this system. At the first level, you will receive 100 EGP per person, at the second level - 200 EGP.\n\n"

        "What are the sponsor's objectives?\n"
        "So that we can pay everyone on our bot, we advertise different people and companies.\n"
        "- In order to actively use our advertising, we also pay you for it. Go to the 'More Money' menu and read"
        "the rules regarding sponsor orders.\n\n"

        "Where will we get the money to pay users?\n"
        " is simple. Cryptocurrencies bring in a lot of money today. That's why we came up with this method of mining cryptocurrency, "
        "so that all participants would make a profit.\n"
        "In addition, we advertise to various bloggers and companies closely related to cryptocurrency.\n\n"

        "How long will it take for the money to be transferred to my account?\n"
        "- It takes 3-7 business days, depending on the load on the payment systems.\n\n"

        "!! An important condition for successful withdrawal !!\n"
        "- You must subscribe to our sponsor's channel and view every new post on his channel within 2 days. "
        "You can find the channel by clicking the 'More money' button."
    )

    # Отправляем сообщение с FAQ
    await message.answer(faq_text)


# Обработчик для кнопки "Профиль"
async def profile_handler(message: Message):
    # Получаем информацию о пользователе из базы данных
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Извлекаем информацию о пользователе, включая balance_egp
    cursor.execute(
        "SELECT username, balance_hash, balance_egp, miner_level, total_referrals FROM users WHERE user_id = ?",
        (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        username = user[0] if user[0] else "Не указано"
        balance_hash = user[1]
        balance_egp = user[2]  # Теперь у нас есть баланс EGP
        miner_level = user[3]
        total_referrals = user[4]  # Если вы добавляли столбец для рефералов

        profile_text = (
            f"👤 My profile:\n"
            f"🏷️ Name: {username}\n"
            f"💰 EGP balance: {balance_egp}\n"
            f"💎 Hash balance: {balance_hash}\n"
            f"⛏️ Miner's level: {miner_level}\n"
            f"👥 Invited friends: {total_referrals}"  # Show the number of invited friends
        )
    else:
        profile_text = "Profile not found. Please try again."

    # Отправляем сообщение с профилем
    await message.answer(profile_text)


# Обработчик для кнопки "Заработать больше"
async def earn_more_handler(message: types.Message):
    await message.answer(
        "💰 DO YOU WANT 1200 EGP FOR A SUBSCRIPTION TO THE CHANNEL?! 📣\n\n"
        "✅ Subscribe to the channel and watch 20 messages, then come back here and \n"
        "👉 click \"Get bonus\". You will receive 1200 EGP 💸\n\n"
        "⚠️ Note: If you unsubscribe, the bonus will not remain 🚫",
        reply_markup=earn_more_inline_keyboard()  # Отправляем инлайн кнопки
    )


# Обработчик для кнопки "Заработать больше"
async def earn_more(message: types.Message):
    await message.answer(
        "🚀 DO YOU WANT TO EARN MORE?! 💰\n\n"
             "✅ Subscribe to the channel and watch 20 messages 👁️",
        reply_markup=earn_more_keyboard()  # Отправляем инлайн кнопки
    )


async def withdrawals_handler(message: Message):
    # Отправляем клавиатуру с банками
    await message.answer("Select a bank for withdrawal:", reply_markup=withdrawals_keyboard())


async def exchange_coins_handler(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance_hash FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        balance_hash = user_data[0]
        max_egp = balance_hash // 200  # Курс: 200 хэш = 1 EGP

        await message.answer(
            f"💱 Enter the EGP amount you want to exchange with coins\n"
            f"💰 Your available balance: {balance_hash} coins\n"
            f"⬆️ Maximum amount: {max_egp} EGP\n"
            f"🔄 Exchange rate: 200 hash = 1 EGP",
            reply_markup=cancel_keyboard()  # Кнопка отмены
        )

        # Устанавливаем состояние FSM
        await ExchangeCoins.waiting_for_amount.set()
    else:
        await message.answer("Error: Information about your balance could not be found.")

    conn.close()


async def withdrawall(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance_egp FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        balance_egp = user_data[0]

        # Сохраняем выбранный банк (если нужно)
        selected_bank = message.text  # Банк, который пользователь выбрал
        await state.update_data(selected_bank=selected_bank)

        await message.answer(
            f"Enter the EGP amount you want to withdraw\n"
            f"Your available balance: {balance_egp} EGP\n",
            reply_markup=cancel_keyboard()  # Кнопка отмены
        )

        # Устанавливаем состояние FSM для ожидания суммы
        await Withdrawall.waiting_for_amount.set()

    conn.close()


# Обработчик ввода суммы
async def process_amount_input(message: types.Message, state: FSMContext):
    # Получаем данные о банке и балансе из состояния
    user_data = await state.get_data()
    selected_bank = user_data.get('selected_bank')

    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance_egp FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        balance_egp = user_data[0]

    try:
        # Преобразуем введенную сумму в число
        amount = float(message.text)
    except ValueError:
        await message.answer("Mistake! Please enter the correct withdrawal amount.")
        return

    if amount <= 0:
        await message.answer("Mistake! The amount must be positive.")
    elif amount > balance_egp:
        await message.answer("Mistake! You don't have enough funds in your balance.")
    else:
        await message.answer("For withdrawal, you must have level 3.")

    # Завершаем состояние
    await state.finish()
    conn.close()


async def check_subscription_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Проверяем, получил ли пользователь бонус за подписку
    cursor.execute("SELECT bonus_received FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        bonus_received = user_data[0]

        if bonus_received == 1:
            # Если бонус уже был получен, отправляем сообщение
            await callback_query.answer("You have already received a subscription bonus!")
            await callback_query.message.edit_text("You have already received your subscription bonus.")
        else:
            # Если бонус еще не был получен, начисляем EGP и обновляем флаг
            cursor.execute("UPDATE users SET balance_egp = balance_egp + 1200, bonus_received = 1 WHERE user_id=?",
                           (user_id,))
            conn.commit()

            # Отправляем сообщение о получении бонуса
            await callback_query.answer("Congratulations! You have received a 1200 EGP subscription bonus.")
            await callback_query.message.edit_text("You have successfully subscribed and received 1200 EGP!")

    conn.close()


async def referral_handler(message: Message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/hackaton_kotiki_bot?start=ref_{user_id}"
    await message.answer(
        f"🎉 Invite your friends with your unique link and get bonuses! 🎁\n\n"
             f"🔗 Your link: {referral_link}",
        reply_markup=main_menu_keyboard()
    )


def get_top_players(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Получаем всех пользователей, отсортированных по balance_egp в порядке убывания
    cursor.execute("SELECT user_id, username, balance_egp FROM users ORDER BY balance_egp DESC")
    users = cursor.fetchall()

    # Находим место текущего пользователя
    user_place = None
    for i, user in enumerate(users):
        if user[0] == user_id:
            user_place = i + 1
            break

    # Формируем топ-3 игроков
    top_players = users[:3]
    conn.close()

    return top_players, user_place


def clean_text(text):
    """Обрабатывает текст, чтобы избежать суррогатных пар."""
    return text.encode('utf-16', 'surrogatepass').decode('utf-16')


async def top_handler(message: Message):
    user_id = message.from_user.id

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Получаем пользователей, отсортированных по убыванию баланса
    cursor.execute("SELECT username, balance_egp FROM users ORDER BY balance_egp DESC LIMIT 3")
    top_users = cursor.fetchall()

    # Определяем место текущего пользователя
    cursor.execute("SELECT COUNT(*) FROM users WHERE balance_egp > (SELECT balance_egp FROM users WHERE user_id=?)",
                   (user_id,))
    position = cursor.fetchone()[0] + 1

    conn.close()

    # Формируем текст топа
    response = f"🏆 Today you are in {position}th place!\n\n"
    response += "🎁 To receive a prize, you must be among the top three players in terms of account balance ✨:\n"
    response += "-----------------------------\n"
    prizes = [175000, 135000, 95000]

    for idx, (username, balance) in enumerate(top_users):
        medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉"
        response +=f"{medal} {username}\n Current balance: {balance} EGP\n Prize: {prizes[idx]} EGP\n-----------------------------\n"

    # Обработка строки перед отправкой
    response = clean_text(response)

    await message.answer(response)


# Регистрация всех обработчиков
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=["start"])
    dp.register_message_handler(earn_handler, lambda message: message.text == "🍬Earn")
    dp.register_message_handler(earn_more_handler,
                                lambda message: message.text == "🥂Earn more")  # Убедитесь, что это здесь
    dp.register_message_handler(click_menu_handler, lambda message: message.text == "⛏️Click")
    dp.register_message_handler(level_up_handler, lambda message: message.text == "⬆️lead the miner's node")
    dp.register_message_handler(withdrawals_handler, lambda message: message.text == "💰payout")
    dp.register_message_handler(back_to_menu_handler, lambda message: message.text == "🔙Return to menu")
    dp.register_callback_query_handler(click_handler, lambda c: c.data == "⛏️click")
    dp.register_callback_query_handler(check_subscription_handler, lambda c: c.data == "check_subscription")
    dp.register_message_handler(profile_handler, lambda message: message.text == "🗿Profile")
    dp.register_message_handler(exchange_coins_handler, lambda message: message.text == "💸Coin Exchange")
    dp.register_message_handler(cancel_handler, lambda message: message.text == "cancellation", state="*")
    dp.register_callback_query_handler(check_subscription_handler, lambda c: c.data == "check_subscription")
    dp.register_message_handler(faq_handler, lambda message: message.text == "💎FAQ")
    dp.register_message_handler(process_exchange, state=ExchangeCoins.waiting_for_amount)

    dp.register_message_handler(withdrawall, lambda message: message.text == "AMERIKA FINANCIERA S.A.")
    dp.register_message_handler(withdrawall, lambda message: message.text == "BANCO AZTECA DEL PERU, S.A.")
    dp.register_message_handler(withdrawall, lambda message: message.text == "BANCO CENTRAL DE RESERVA DEL PERU")
    dp.register_message_handler(withdrawall, lambda message: message.text == "BANCO CONTINENTAL")
    dp.register_message_handler(withdrawall, lambda message: message.text == "TRC-20")
    dp.register_message_handler(process_amount_input, state=Withdrawall.waiting_for_amount)
    dp.register_message_handler(earn_more, lambda message: message.text == "✈️Additionally")
    dp.register_message_handler(referral_handler, lambda message: message.text == "🎰Referral")
    dp.register_message_handler(top_handler, lambda message: message.text == "🏆Users Top")
