from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import logging
import json
import sqlite3
import random
import datetime
import string

TOKEN = "7648801895:AAG7U0stJOT5fvATpAjKvdmOUrJApE-G-BY"
DB_FILE = 'scores.db'
POINT_TIERS = {'easy': 100, 'medium': 500, 'hard': 1000}
(
    SELECT_PLAYERS, WAIT_PLAYERS,
    DICE_CHOICE, NUMBER_GUESS,
    SELECT_TIER, SELECT_TOPIC,
    ASK_QUESTION, GAME_OVER
) = range(8)

games = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS results (
            game_id TEXT PRIMARY KEY,
            timestamp TEXT,
            players TEXT,
            scores TEXT
        )''')


def save_game(game_id):
    game = games[game_id]
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            'REPLACE INTO results VALUES (?,?,?,?)',
            (
                game_id,
                datetime.datetime.now().isoformat(),
                json.dumps([p[1] for p in game['players']]),
                json.dumps(game['scores'])
            )
        )


QUESTIONS = {
    "Математика": [
        {"question": "Сколько будет 7 + 5?", "options": ["10", "11", "12", "13"], "answer": 2,
         "points": POINT_TIERS['easy']},
        {"question": "Чему равен корень из 81?", "options": ["7", "8", "9", "10"], "answer": 2,
         "points": POINT_TIERS['easy']},
        {"question": "Вычислите 15 × 12.", "options": ["170", "180", "190", "200"], "answer": 1,
         "points": POINT_TIERS['medium']},
        {"question": "Сумма углов треугольника?", "options": ["90°", "180°", "270°", "360°"], "answer": 1,
         "points": POINT_TIERS['easy']},
        {"question": "Решите 2x - 4 = 10.", "options": ["3", "6", "7", "8"], "answer": 2,
         "points": POINT_TIERS['medium']},
        {"question": "log₂32 = ?", "options": ["4", "5", "6", "8"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Площадь круга радиус 4.", "options": ["8π", "12π", "16π", "20π"], "answer": 2,
         "points": POINT_TIERS['medium']},
        {"question": "Простых чисел <20?", "options": ["7", "8", "9", "10"], "answer": 1,
         "points": POINT_TIERS['hard']},
        {"question": "3⁵ = ?", "options": ["243", "125", "81", "312"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "(x+2)(x-2) при x=5.", "options": ["21", "25", "27", "35"], "answer": 0,
         "points": POINT_TIERS['hard']}
    ],
    "История": [
        {"question": "Крещение Руси в каком году?", "options": ["988", "989", "990", "991"], "answer": 0,
         "points": POINT_TIERS['easy']},
        {"question": "Начало ВОВ?", "options": ["1939", "1940", "1941", "1942"], "answer": 2,
         "points": POINT_TIERS['easy']},
        {"question": "Первый император Рима?", "options": ["Цезарь", "Август", "Нерон", "Тиберий"], "answer": 1,
         "points": POINT_TIERS['medium']},
        {"question": "Падение Западной Римской империи?", "options": ["476", "486", "496", "506"], "answer": 0,
         "points": POINT_TIERS['medium']},
        {"question": "Французская революция?", "options": ["1789", "1799", "1804", "1815"], "answer": 0,
         "points": POINT_TIERS['easy']},
        {"question": "Лидер после Ленина?", "options": ["Хрущев", "Сталин", "Маленков", "Берия"], "answer": 1,
         "points": POINT_TIERS['hard']},
        {"question": "Основание СПб?", "options": ["1703", "1710", "1721", "1730"], "answer": 0,
         "points": POINT_TIERS['medium']},
        {"question": "Историю государства Российского написал?",
         "options": ["Карамзин", "Толстой", "Всеволодов", "Пушкин"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Принятие Конституции РФ 1993?", "options": ["1991", "1992", "1993", "1994"], "answer": 2,
         "points": POINT_TIERS['medium']},
        {"question": "Леонардо да Винчи жил в век?", "options": ["14", "15", "16", "17"], "answer": 2,
         "points": POINT_TIERS['hard']}
    ],
    "Наука": [
        {"question": "Единица измерения силы в СИ?", "options": ["Ньютон", "Джоуль", "Вольт", "Ватт"], "answer": 0,
         "points": POINT_TIERS['easy']},
        {"question": "Скорость света в вакууме примерно?",
         "options": ["3×10⁸ м/с", "3×10⁶ м/с", "3×10⁷ м/с", "3×10⁵ м/с"], "answer": 0,
         "points": POINT_TIERS['easy']},
        {"question": "Формула закона всемирного тяготения Ньютона?",
         "options": ["F=ma", "F=Gm₁m₂/r²", "E=mc²", "pV=nRT"], "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Что изучает ботаника?", "options": ["Растения", "Животные", "Грибы", "Бактерии"], "answer": 0,
         "points": POINT_TIERS['easy']},
        {"question": "Элемент с атомным номером 6?", "options": ["Углерод", "Кислород", "Азот", "Водород"],
         "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Период полураспада урана-238?",
         "options": ["4.5 млрд лет", "4.5 млн лет", "4500 лет", "450 лет"], "answer": 0,
         "points": POINT_TIERS['hard']},
        {"question": "Основная функция митохондрий?",
         "options": ["Энергетика клетки", "Синтез белка", "Деление клетки", "Хранение ДНК"], "answer": 0,
         "points": POINT_TIERS['medium']},
        {"question": "Закон Ома для участка цепи?", "options": ["U=IR", "P=UI", "Q=cmΔT", "E=mc²"], "answer": 0,
         "points": POINT_TIERS['easy']},
        {"question": "Что изучает зоология?", "options": ["Животных", "Растения", "Минералы", "Вирусы"],
         "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Основной газ атмосферы Земли?", "options": ["Азот", "Кислород", "CO₂", "Водород"],
         "answer": 0, "points": POINT_TIERS['medium']}
    ],
    "География": [
        {"question": "Столица Франции?", "options": ["Берлин", "Париж", "Рим", "Мадрид"], "answer": 1,
         "points": POINT_TIERS['easy']},
        {"question": "Самый длинный континентальный хребет?",
         "options": ["Анды", "Гималаи", "Альпы", "Скалистые горы"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Где находится Марианская впадина?",
         "options": ["Тихий океан", "Атлантический", "Индийский", "Северный ледовитый"], "answer": 0,
         "points": POINT_TIERS['medium']},
        {"question": "Через какую страну не протекает река Дунай?",
         "options": ["Германия", "Франция", "Румыния", "Венгрия"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Крупнейшее озеро Африки?", "options": ["Виктория", "Танганьика", "Малави", "Ньяса"],
         "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Самая высокая точка России?", "options": ["Эльбрус", "Казбек", "Дхаулагири", "Аннапурна"],
         "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Столица Австралии?", "options": ["Сидней", "Мельбурн", "Канберра", "Брисбен"], "answer": 2,
         "points": POINT_TIERS['easy']},
        {"question": "Какой материк самый большой?", "options": ["Азия", "Африка", "Европа", "Антарктида"],
         "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "На каком материке находится пустыня Гоби?",
         "options": ["Азия", "Африка", "Северная Америка", "Австралия"], "answer": 0,
         "points": POINT_TIERS['medium']},
        {"question": "Какой океан самый мелкий?",
         "options": ["Северный ледовитый", "Индийский", "Атлантический", "Тихий"], "answer": 0,
         "points": POINT_TIERS['hard']}
    ],
    "Культура": [
        {"question": "Автор 'Евгения Онегина'?", "options": ["Пушкин", "Толстой", "Достоевский", "Гоголь"],
         "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Кто написал 'Войну и мир'?", "options": ["Пушкин", "Гоголь", "Толстой", "Тургенев"],
         "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Режиссер фильма 'Интерстеллар'?", "options": ["Нолан", "Кэмерон", "Содерберг", "Спилберг"],
         "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Какой художник создал 'Звездную ночь'?",
         "options": ["Ван Гог", "Пикассо", "Рембрандт", "Монет"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Композитор 'Лунной сонаты'?", "options": ["Бетховен", "Моцарт", "Бах", "Чайковский"],
         "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Автор цикла романов 'Песнь льда и пламени'?",
         "options": ["Толкиен", "Мартин", "Роулинг", "Кинг"], "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Какой стиль архитектуры характерен для собора Парижской Богоматери?",
         "options": ["Готика", "Барокко", "Классицизм", "Ренессанс"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Кто сочинил оперу 'Кармен'?", "options": ["Бизе", "Моцарт", "Верди", "Чайковский"],
         "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Жанр романа '1984'?", "options": ["Антиутопия", "Фантастика", "Драма", "Комедия"],
         "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Кто написал 'Мастер и Маргарита'?",
         "options": ["Булгаков", "Пушкин", "Достоевский", "Гоголь"], "answer": 0, "points": POINT_TIERS['medium']}
    ],
}


def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def roll_dice():
    return random.randint(1, 6)


def restart_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Перезапустить", callback_data="force_restart")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("1"), KeyboardButton("2")]],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎮 Выберите количество игроков:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🎮 Выберите количество игроков:",
            reply_markup=reply_markup
        )
    return SELECT_PLAYERS


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start(update, context)


async def select_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        players_count = int(update.message.text)
        if players_count not in [1, 2]:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Выберите 1 или 2", reply_markup=restart_keyboard())
        return SELECT_PLAYERS

    game_id = generate_id()
    games[game_id] = {
        'players': [(update.effective_user.id, update.effective_user.full_name)],
        'scores': [0] * players_count,
        'chat_id': update.effective_chat.id,
        'dice': None,
        'choices': {},
        'current_player': 0,
        'questions': [],
        'current_question': 0
    }
    context.user_data['game_id'] = game_id

    if players_count == 2:
        bot = await context.bot.get_me()
        invite_link = f"https://t.me/{bot.username}?start={game_id}"
        await update.message.reply_text(
            f"🔗 Пригласите второго игрока:\n{invite_link}",
            reply_markup=restart_keyboard()
        )
        return WAIT_PLAYERS

    return await start_single_player(update, context)


async def start_single_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_id = context.user_data['game_id']
    games[game_id]['dice'] = roll_dice()
    await context.bot.send_message(
        chat_id=games[game_id]['chat_id'],
        text=f"🎲 Выпало: {games[game_id]['dice']}\nВыберите четность:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Чёт", callback_data="even"),
             InlineKeyboardButton("Нечёт", callback_data="odd")]
        ])
    )

    return DICE_CHOICE


async def join_existing_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_id = context.args[0]
    if game_id not in games:
        await update.message.reply_text("❌ Игра не найдена!")
        return ConversationHandler.END

    user = update.effective_user
    games[game_id]['players'].append((user.id, user.full_name))

    if len(games[game_id]['players']) == 2:
        await context.bot.send_message(
            games[game_id]['chat_id'],
            f"🌟 Игрок 2 ({user.full_name}) присоединился!"
        )
        games[game_id]['dice'] = roll_dice()
        await context.bot.send_message(
            games[game_id]['chat_id'],
            f"🎲 Выпало: {games[game_id]['dice']}\nВыберите четность:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Чёт", callback_data="even"),
                 InlineKeyboardButton("Нечёт", callback_data="odd")]
            ])
        )
        return DICE_CHOICE

    await update.message.reply_text("⏳ Ожидаем второго игрока...")
    return WAIT_PLAYERS


async def handle_dice_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_id = context.user_data['game_id']
    user_id = query.from_user.id

    if user_id not in [p[0] for p in games[game_id]['players']]:
        await query.message.reply_text("❌ Вы не участник этой игры!")
        return

    choice = query.data
    games[game_id]['choices'][user_id] = choice

    if len(games[game_id]['choices']) < len(games[game_id]['players']):
        return
    dice = games[game_id]['dice']
    correct_answer = "even" if dice % 2 == 0 else "odd"

    results = []
    for player_id, player_choice in games[game_id]['choices'].items():
        if player_choice == correct_answer:
            results.append((player_id, True))
        else:
            results.append((player_id, False))

    response = ["Результаты угадывания:"]
    for player_id, is_correct in results:
        name = next(p[1] for p in games[game_id]['players'] if p[0] == player_id)
        result = "✅ Угадал" if is_correct else "❌ Не угадал"
        response.append(f"{name}: {result}")

    await context.bot.send_message(
        games[game_id]['chat_id'],
        "\n".join(response)
    )

    await context.bot.send_message(
        games[game_id]['chat_id'],
        "🔢 Теперь угадайте число от 1 до 6:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i), callback_data=f"num_{i}") for i in range(1, 4)],
            [InlineKeyboardButton(str(i), callback_data=f"num_{i}") for i in range(4, 7)]
        ])
    )
    return NUMBER_GUESS


async def handle_number_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_id = context.user_data['game_id']
    user_id = query.from_user.id
    number = int(query.data.split('_')[1])

    games[game_id]['choices'][user_id] = number

    if len(games[game_id]['choices']) < len(games[game_id]['players']):
        return

    dice = games[game_id]['dice']
    closest = min(
        games[game_id]['choices'].values(),
        key=lambda x: abs(x - dice)
    )

    winners = []
    for player_id, guess in games[game_id]['choices'].items():
        if guess == closest:
            winners.append(player_id)
    response = [f"🎲 Выпало число: {dice}", "Результаты угадывания:"]
    for player_id, guess in games[game_id]['choices'].items():
        name = next(p[1] for p in games[game_id]['players'] if p[0] == player_id)
        result = "🎯 Точное попадание!" if guess == dice else f"Ваш выбор: {guess}"
        response.append(f"{name}: {result}")

    if len(winners) == 1:
        winner_id = winners[0]
        winner_name = next(p[1] for p in games[game_id]['players'] if p[0] == winner_id)
        response.append(f"\n🏆 Победитель: {winner_name}!")
        games[game_id]['current_player'] = games[game_id]['players'].index(
            next(p for p in games[game_id]['players'] if p[0] == winner_id))
    else:
        response.append("\n🤝 Ничья! Первый игрок выбирает категорию")
        games[game_id]['current_player'] = 0

    await context.bot.send_message(
        games[game_id]['chat_id'],
        "\n".join(response)
    )

    return await select_difficulty(context, game_id)


async def select_difficulty(context: ContextTypes.DEFAULT_TYPE, game_id: str):
    buttons = [
        [InlineKeyboardButton(
            f"{tier.title()} ({points} очков)",
            callback_data=f"tier_{tier}"
        )]
        for tier, points in POINT_TIERS.items()
    ]

    await context.bot.send_message(
        chat_id=games[game_id]['chat_id'],
        text="🎚 Выберите сложность:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_TIER


async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_id = context.user_data['game_id']
    tier = query.data.split('_')[1]
    games[game_id]['tier'] = tier
    games[game_id]['points'] = POINT_TIERS[tier]
    return await select_topic(context, game_id)


async def select_topic(context: ContextTypes.DEFAULT_TYPE, game_id: str):
    buttons = [
        [InlineKeyboardButton(topic, callback_data=f"topic_{topic}")]
        for topic in QUESTIONS.keys()
    ]

    await context.bot.send_message(
        chat_id=games[game_id]['chat_id'],
        text="📚 Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_TOPIC


async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_id = context.user_data['game_id']
    topic = query.data.split('_')[1]

    game = games[game_id]
    game['questions'] = [
        q for q in QUESTIONS[topic]
        if q['points'] == game['points']
    ]
    random.shuffle(game['questions'])
    game['current_question'] = 0
    return await ask_question(context, game_id)


async def ask_question(context: ContextTypes.DEFAULT_TYPE, game_id: str):
    game = games[game_id]
    if game['current_question'] >= len(game['questions']):
        return await finish_game(context, game_id)

    question = game['questions'][game['current_question']]
    player_index = game['current_question'] % len(game['players'])
    player_name = game['players'][player_index][1]

    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"ans_{i}")]
        for i, opt in enumerate(question['options'])
    ]

    await context.bot.send_message(
        game['chat_id'],
        f"🧠 {player_name}, вопрос за {question['points']} очков:\n{question['question']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ASK_QUESTION


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_id = context.user_data['game_id']
    game = games[game_id]
    question = game['questions'][game['current_question']]
    answer_index = int(query.data.split('_')[1])

    player_index = game['current_question'] % len(game['players'])
    if answer_index == question['answer']:
        game['scores'][player_index] += question['points']
    else:
        game['scores'][player_index] -= question['points'] // 2

    game['current_question'] += 1
    await query.edit_message_reply_markup()
    return await ask_question(context, game_id)


async def finish_game(context: ContextTypes.DEFAULT_TYPE, game_id: str):
    game = games[game_id]
    results = "\n".join(
        f"🏅 {name}: {score} очков"
        for (_, name), score in zip(game['players'], game['scores'])
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Новая игра", callback_data="new_game"),
         InlineKeyboardButton("🏠 Выход", callback_data="exit")]
    ])

    await context.bot.send_message(
        game['chat_id'],
        f"🏁 Игра завершена!\n\n{results}",
        reply_markup=buttons
    )

    save_game(game_id)
    del games[game_id]
    return GAME_OVER


async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "new_game":
        context.user_data.clear()
        await query.edit_message_text("🔄 Начинаем новую игру...")
        return await start(update, context)

    await query.edit_message_text("🚪 Выход в главное меню")
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Произошла ошибка. Попробуйте перезапустить бота:",
            reply_markup=restart_keyboard()
        )
    return ConversationHandler.END


def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(restart_callback, pattern='^force_restart$')
        ],
        states={
            SELECT_PLAYERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_players)],
            WAIT_PLAYERS: [CommandHandler('start', join_existing_game)],
            DICE_CHOICE: [CallbackQueryHandler(handle_dice_choice, pattern=r'^(even|odd)$')],
            NUMBER_GUESS: [CallbackQueryHandler(handle_number_guess, pattern=r'^num_')],
            SELECT_TIER: [CallbackQueryHandler(handle_difficulty, pattern=r'^tier_')],
            SELECT_TOPIC: [CallbackQueryHandler(handle_topic, pattern=r'^topic_')],
            ASK_QUESTION: [CallbackQueryHandler(handle_answer, pattern=r'^ans_')],
            GAME_OVER: [CallbackQueryHandler(handle_restart, pattern=r'^(new_game|exit|force_restart)$')]
        },
        fallbacks=[CommandHandler('start', start)],
        per_message=False
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
