import sqlite3
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from keyboards import earn_menu_keyboard, earn_more_keyboard, cancel_keyboard, withdrawals_keyboard, click_inline_keyboard, main_menu_keyboard, earn_more_inline_keyboard
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
        "Добро пожаловать! Вы успешно зарегистрированы.",
        reply_markup=main_menu_keyboard()
    )


# Обработчик для кнопки "Зарабатывать"
async def earn_handler(message: Message):
    await message.answer("Выберите действие:", reply_markup=earn_menu_keyboard())  # Меню с обычными кнопками


# Обработчик для нажатия на кнопку "Click" в обычном меню
async def click_menu_handler(message: Message):
    await message.answer("Вы начали процесс клика! Нажмите на кнопку ниже:", reply_markup=click_inline_keyboard())


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
                "Вы выполнили 100 из 100 возможных заданий.\n"
                "Новые миссии появятся в течение 24 часов.\n"
                "Вы можете заработать намного больше денег на этом канале.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Зарабатывать деньги", url="https://t.me/your_channel_link")
                )
            )
            # Отправляем ответ на клик
            await callback_query.answer("Вы достигли лимита кликов на сегодня.")
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
                f"Сегодня: {clicks_today} / 100\n"
                f"Прогресс: {progress}%\n"
                f"Coins за клик: {coins_per_click}\n"
                f"Уровень Шахтера: {miner_level}\n"
                f"Баланс хэша: {balance_hash}"
            )

            # Попробуем обновить сообщение с информацией
            try:
                await callback_query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Click", callback_data="click")
                    )
                )
            except Exception as e:
                print(f"Ошибка при редактировании сообщения: {e}")

            # Отправляем ответ на клик
            await callback_query.answer("Вы нажали на кнопку Click!")

    else:
        # Если пользователь не найден, уведомляем об этом
        await callback_query.answer("Пользователь не найден. Пожалуйста, зарегистрируйтесь.")

    conn.close()


async def process_exchange(message: Message, state: FSMContext):
    user_id = message.from_user.id
    amount = message.text

    try:
        amount = int(amount)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")
        return

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance_hash FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        balance_hash = user_data[0]
        max_egp = balance_hash // 200  # Курс обмена

        if amount <= 0:
            await message.answer("Сумма обмена не может быть отрицательной или нулевой.")
        elif amount > max_egp:
            await message.answer(f"Вы можете обменять не более {max_egp} EGP.")
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
                    f"Успешно обменено {amount} EGP\n"
                    f"Ваш новый баланс: {balance_egp} EGP"
                )
            else:
                await message.answer("Ошибка при обновлении вашего баланса.")
        await state.finish()  # Завершаем состояние
    conn.close()



async def cancel_handler(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu_keyboard())

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
                cursor.execute("UPDATE users SET miner_level=?, balance_hash=? WHERE user_id=?", (miner_level, balance_hash, user_id))
                conn.commit()

                # Отправляем сообщение о повышении уровня
                await message.answer(
                    f"Поздравляю! Ваш уровень майнера повысился до {miner_level}. "
                    f"Теперь вы получаете в 2 раза больше хэша за клик.",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Повысить уровень майнера", callback_data="level_up")
                    )
                )
            else:
                # Если недостаточно средств для улучшения
                await message.answer(
                    f"Вам не хватает {next_level_cost - balance_hash} монет для повышения уровня. "
                    f"Необходимая сумма для улучшения: {next_level_cost}.",
                )
        else:
            # Если достигнут максимальный уровень
            await message.answer(
                "У вас максимальный уровень майнера. Дальше улучшений не предусмотрено."
            )
    conn.close()



# Обработчик для возвращения в меню
async def back_to_menu_handler(message: Message):
    await message.answer("Вы вернулись в основное меню.", reply_markup=main_menu_keyboard())


# Обработчик для кнопки "FAQ"
async def faq_handler(message: Message):
    # Формируем сообщение с FAQ
    faq_text = (
        "Что это за бот?\n"
        "- С помощью этого Telegram-бота вы можете зарабатывать деньги, нажав кнопку 'Click'.\n\n"

        "Как это работает?\n"
        "- Это довольно просто. Каждый ваш клик получает определенную мощность на наших серверах, "
        "что позволяет вам добывать криптовалюту в кратчайшие сроки.\n\n"

        "Как начать зарабатывать?\n"
        "- Это просто! Нажмите кнопку 'Майнинг', а затем нажмите кнопку 'Нажмите'.\n"
        "- За каждый клик вы будете получать определенное количество coins, что в будущем позволит вам "
        "конвертировать coins в биткойны, а затем обменять биткойны на EGP и вывести деньги.\n\n"

        "У меня есть определенное количество coins, что дальше?\n"
        "- Тогда вам нужно нажать кнопку 'Обмен coins' и обменять coins на Bitcoin.\n\n"

        "Как обменять биткоины на EGP? Как вывести деньги?\n"
        "- Чтобы вывести деньги, вам нужно зайти в главное меню и нажать кнопку 'Вывод средств'. "
        "Затем выберите любой удобный для вас способ получения своих денег.\n"
        "- !!! Помните, что вывод доступен с 3 уровня !!!\n\n"

        "Как повысить уровень и почему?\n"
        "- Каждый уровень позволяет вам получать больше coins за клик. Например, на первом уровне вы получаете 25 coins за клик, "
        "на втором уровне - 60 coins. Кроме того, вам нужен уровень 3, чтобы вывести деньги.\n"
        "- Для повышения уровня у вас должно быть определенное количество coins. Например, чтобы перейти на второй уровень, "
        "вам необходимо иметь 12500 coins. Если у вас есть такое количество coins, перейдите в меню 'Майнинг' и нажмите кнопку "
        "'Улучшить уровень майнера', а затем кнопку 'Обновить'.\n\n"

        "Как зарабатывать больше?\n"
        "- Чтобы зарабатывать больше, мы ввели реферальную систему и задания от спонсоров.\n\n"

        "Как заработать в реферальной системе?\n"
        "- Для этого вам в меню придет персональная ссылка 'Деньги другу'. Возьмите эту ссылку, отправьте ее своим друзьям "
        "или разместите в различных источниках: например, в Facebook или Tik-Tok.\n"
        "- В этой системе также есть уровни. На первом уровне вы получите 100 EGP на человека, на втором уровне - 200 EGP.\n\n"

        "Каковы задачи спонсора?\n"
        "- Чтобы мы могли платить всем на нашем боте, мы рекламируем разных людей и компании.\n"
        "- Чтобы активно использовать нашу рекламу, мы также платим вам за это. Перейдите в меню 'Больше денег' и ознакомьтесь "
        "с правилами относительно заказов от спонсора.\n\n"

        "Откуда мы возьмем деньги для оплаты пользователям?\n"
        "- Это просто. Сегодня криптовалюты приносят огромные деньги. Вот почему мы придумали этот метод добычи криптовалюты, "
        "чтобы все участники получали прибыль.\n"
        "- Кроме того, мы даем рекламу различным блогерам и компаниям, тесно связанным с криптовалютой.\n\n"

        "Сколько времени потребуется, чтобы деньги были переведены на мой счет?\n"
        "- Это занимает 3-7 рабочих дней, в зависимости от нагрузки на платежные системы.\n\n"

        "!! Важное условие успешного вывода !!\n"
        "- Вы должны подписаться на канал нашего спонсора и просматривать каждый новый пост на его канале в течение 2 дней. "
        "Найти канал можно, нажав кнопку 'Больше денег'."
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
    cursor.execute("SELECT username, balance_hash, balance_egp, miner_level, total_referrals FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        username = user[0] if user[0] else "Не указано"
        balance_hash = user[1]
        balance_egp = user[2]  # Теперь у нас есть баланс EGP
        miner_level = user[3]
        total_referrals = user[4]  # Если вы добавляли столбец для рефералов

        profile_text = (
            f"Мой профиль:\n"
            f"Имя: {username}\n"
            f"EGP баланс: {balance_egp}\n"
            f"Хэш-баланс: {balance_hash}\n"
            f"Уровень Шахтера: {miner_level}\n"
            f"Приглашенные друзья: {total_referrals}"  # Показываем количество приглашенных друзей
        )
    else:
        profile_text = "Профиль не найден. Пожалуйста, попробуйте снова."

    # Отправляем сообщение с профилем
    await message.answer(profile_text)

# Обработчик для кнопки "Заработать больше"
async def earn_more_handler(message: types.Message):
    await message.answer(
        "ХОТИТЕ 1200 EGP ЗА ПОДПИСКУ НА КАНАЛ ?! !\n\n"
        "Подпишитесь на канал и посмотрите 20 сообщений, затем вернитесь сюда и\n"
        "нажмите \"Получить бонус\". Вы получите 1200 EGP\n\n"
        "!! Примечание: Если вы откажетесь от подписки, бонус не останется",
        reply_markup=earn_more_inline_keyboard()  # Отправляем инлайн кнопки
    )


# Обработчик для кнопки "Заработать больше"
async def earn_more(message: types.Message):
    await message.answer(
        "ХОТИТЕ ЗАРАБОТАТЬ БОЛЬШЕ?! !\n\n"
        "Подпишитесь на канал и посмотрите 20 сообщений",
        reply_markup=earn_more_keyboard()  # Отправляем инлайн кнопки
    )
async def withdrawals_handler(message: Message):
    # Отправляем клавиатуру с банками
    await message.answer("Выберите банк для вывода:", reply_markup=withdrawals_keyboard())


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
            f"Введите сумму EGP, которую хотите обменять с coins\n"
            f"Ваш доступный баланс: {balance_hash} coins\n"
            f"Максимальная сумма: {max_egp} EGP\n"
            f"Курс обмена: 200 hash = 1 EGP",
            reply_markup=cancel_keyboard()  # Кнопка отмены
        )

        # Устанавливаем состояние FSM
        await ExchangeCoins.waiting_for_amount.set()
    else:
        await message.answer("Ошибка: Не удалось найти информацию о вашем балансе.")

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
            f"Введите сумму EGP, которую хотите вывести\n"
            f"Ваш доступный баланс: {balance_egp} EGP\n",
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
        await message.answer("Ошибка! Пожалуйста, введите корректную сумму для вывода.")
        return

    if amount <= 0:
        await message.answer("Ошибка! Сумма должна быть положительной.")
    elif amount > balance_egp:
        await message.answer("Ошибка! У вас недостаточно средств на балансе.")
    else:
            await message.answer("Для вывода у вас должен быть 3 уровень.")

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
            await callback_query.answer("Вы уже получили бонус за подписку!")
            await callback_query.message.edit_text("Вы уже получили ваш бонус за подписку.")
        else:
            # Если бонус еще не был получен, начисляем EGP и обновляем флаг
            cursor.execute("UPDATE users SET balance_egp = balance_egp + 1200, bonus_received = 1 WHERE user_id=?", (user_id,))
            conn.commit()

            # Отправляем сообщение о получении бонуса
            await callback_query.answer("Поздравляю! Вы получили бонус 1200 EGP за подписку.")
            await callback_query.message.edit_text("Вы успешно подписались и получили 1200 EGP!")

    conn.close()

async def referral_handler(message: Message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/hackaton_kotiki_bot?start=ref_{user_id}"
    await message.answer(
        f"Приглашайте друзей с вашей уникальной ссылкой и получайте бонусы!\n\n"
        f"Ваша ссылка: {referral_link}",
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
    cursor.execute("SELECT COUNT(*) FROM users WHERE balance_egp > (SELECT balance_egp FROM users WHERE user_id=?)", (user_id,))
    position = cursor.fetchone()[0] + 1

    conn.close()

    # Формируем текст топа
    response = f"🏆 Сегодня вы находитесь на {position}-м месте!\n\n"
    response += "🎁 Чтобы получить приз, вы должны быть в тройке лучших игроков по балансу счета ✨:\n"
    response += "-----------------------------\n"
    prizes = [175000, 135000, 95000]

    for idx, (username, balance) in enumerate(top_users):
        medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉"
        response += f"{medal} {username}\nТекущий баланс: {balance} EGP\nПриз: {prizes[idx]} EGP\n-----------------------------\n"

    # Обработка строки перед отправкой
    response = clean_text(response)

    await message.answer(response)



# Регистрация всех обработчиков
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=["start"])
    dp.register_message_handler(earn_handler, lambda message: message.text == "Зарабатывать")
    dp.register_message_handler(earn_more_handler, lambda message: message.text == "Заработать больше")  # Убедитесь, что это здесь
    dp.register_message_handler(click_menu_handler, lambda message: message.text == "Click")
    dp.register_message_handler(level_up_handler, lambda message: message.text == "Повысить уровень майнера")
    dp.register_message_handler(withdrawals_handler, lambda message: message.text == "Выплаты")
    dp.register_message_handler(back_to_menu_handler, lambda message: message.text == "Вернуться в меню")
    dp.register_callback_query_handler(click_handler, lambda c: c.data == "click")
    dp.register_callback_query_handler(check_subscription_handler, lambda c: c.data == "check_subscription")
    dp.register_message_handler(profile_handler, lambda message: message.text == "Профиль")
    dp.register_message_handler(exchange_coins_handler, lambda message: message.text == "Обмен Coins")
    dp.register_message_handler(cancel_handler, lambda message: message.text == "Отмена", state="*")
    dp.register_callback_query_handler(check_subscription_handler, lambda c: c.data == "check_subscription")
    dp.register_message_handler(faq_handler, lambda message: message.text == "FAQ")
    dp.register_message_handler(process_exchange, state=ExchangeCoins.waiting_for_amount)

    dp.register_message_handler(withdrawall, lambda message: message.text == "AMERIKA FINANCIERA S.A.")
    dp.register_message_handler(withdrawall, lambda message: message.text == "BANCO AZTECA DEL PERU, S.A.")
    dp.register_message_handler(withdrawall, lambda message: message.text == "BANCO CENTRAL DE RESERVA DEL PERU")
    dp.register_message_handler(withdrawall, lambda message: message.text == "BANCO CONTINENTAL")
    dp.register_message_handler(withdrawall, lambda message: message.text == "TRC-20")
    dp.register_message_handler(process_amount_input, state=Withdrawall.waiting_for_amount)
    dp.register_message_handler(earn_more, lambda message: message.text == "Дополнительно")
    dp.register_message_handler(referral_handler, lambda message: message.text == "Рефералка")
    dp.register_message_handler(top_handler, lambda message: message.text == "Топ пользователей")