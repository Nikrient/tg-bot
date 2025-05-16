from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes
)
import logging
import sqlite3
import datetime
import random
TOKEN = "BOT_TOKEN"
DB_FILE = 'scores.db'
POINT_TIERS = {'easy': 100, 'medium': 500, 'hard': 1000}
(
    SELECT_TIER,
    SELECT_TOPIC,
    ASK_QUESTION,
    GAME_OVER
) = range(4)

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
            topic TEXT,
            score INTEGER
        )''')


def save_game(game_id):
    game = games[game_id]
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            'REPLACE INTO results VALUES (?,?,?,?)',
            (
                game_id,
                datetime.datetime.now().isoformat(),
                game['topic'],
                game['score']
            )
        )

QUESTIONS = {
    "Математика": [
        {"question": "Сколько будет 8 + 7?",       "options": ["13","14","15","16"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "12 − 5 = ?",                  "options": ["6","7","8","9"],     "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Сколько будет 6 × 2?",       "options": ["10","12","14","16"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "9 ÷ 3 = ?",                  "options": ["2","3","4","5"],     "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "2 + 3 + 4 = ?",              "options": ["7","8","9","10"],    "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "15 − 7 = ?",                 "options": ["6","7","8","9"],     "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Сколько будет 5 + 9?",       "options": ["13","14","15","16"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Вычислите 14 × 6.",           "options": ["74","84","94","104"], "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "56 ÷ 8 = ?",                  "options": ["6","7","8","9"],     "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Сумма углов квадрата?",      "options": ["180°","270°","360°","450°"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Площадь прямоугольника 4×7.", "options": ["11","21","28","32"],   "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Среднее арифметическое 4,6,8?", "options": ["5","6","7","8"],   "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Вычислите 9² − 5².",           "options": ["16","25","56","106"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Корень из 144 = ?",           "options": ["10","11","12","13"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "log₂16 = ?",                  "options": ["2","3","4","5"],     "answer": 2, "points": POINT_TIERS['hard']},
        {"question": "3⁴ = ?",                      "options": ["27","64","81","108"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "sin 30° =",                   "options": ["½","√2/2","√3/2","1"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Чему равен 7C2?",             "options": ["21","14","35","28"],  "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Значение e⁰ = ?",             "options": ["0","1","e","e²"],     "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "log₁₀1000 =",                 "options": ["1","2","3","4"],     "answer": 2, "points": POINT_TIERS['hard']},
        {"question": "Процент от числа: 15% от 200?", "options": ["20","25","30","35"], "answer": 2, "points": POINT_TIERS['hard']},
    ],

    "История": [
        {"question": "Год открытия Америки Колумбом?",     "options": ["1490","1492","1500","1502"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Год крещения Руси?",                "options": ["987","988","989","990"],     "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Начало Первой мировой войны?",       "options": ["1912","1914","1916","1918"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Год падения Рима (западная часть)?", "options": ["455","465","476","486"],     "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Кто был первым президентом США?",    "options": ["Джефферсон","Адамс","Вашингтон","Линкольн"], "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Год Французской революции?",        "options": ["1776","1789","1799","1804"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Год Великой Октябрьской социалистической революции?", "options": ["1915","1917","1919","1921"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Год провозглашения Наполеона императором?", "options": ["1799","1802","1804","1806"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Год издания Библии короля Якова?",     "options": ["1600","1604","1611","1620"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Где проходила битва при Гастингсе?", "options": ["Франция","Англия","Нормандия","Шотландия"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Кто возглавил СССР после Ленина?",     "options": ["Каменева","Троцкого","Сталин","Маленков"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Год начала Крымской войны?",           "options": ["1842","1853","1861","1870"], "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Год провозглашения США независимыми?", "options": ["1776","1783","1791","1801"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Падение Берлинской стены произошло в?", "options": ["1987","1988","1989","1990"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Год битвы при Ватерлоо?",           "options": ["1812","1815","1820","1825"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Автор \"Истории государства Российского\"?", "options": ["Ломоносов","Карамзин","Толстой","Соловьев"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Год подписания Версальского договора?", "options": ["1917","1918","1919","1920"], "answer": 2, "points": POINT_TIERS['hard']},
        {"question": "Кто возглавил Францию после Наполеона Бонапарта?", "options": ["Людовик XVIII","Шарль X","Наполеон III","Луи-Филипп"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Год убийства Юлия Цезаря?",           "options": ["44 до н.э.","42 до н.э.","40 до н.э.","38 до н.э."], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Где был заключён Потсдамский мир?",   "options": ["Варшава","Париж","Потсдам","Берлин"], "answer": 2, "points": POINT_TIERS['hard']},
        {"question": "Год образования Лиги Наций?",        "options": ["1917","1918","1919","1920"], "answer": 2, "points": POINT_TIERS['hard']},
    ],

    "Наука": [
        {"question": "Единица измерения силы?",      "options": ["Ньютон","Джоуль","Вольт","Ватт"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Скорость света примерно?",    "options": ["3×10⁵","3×10⁶","3×10⁷","3×10⁸ м/с"], "answer": 3, "points": POINT_TIERS['easy']},
        {"question": "Единица измерения массы?",    "options": ["Килограмм","Метр","Литр","Секунда"],   "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Сколько планет в Солнечной системе?", "options": ["7","8","9","10"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Основной газ атмосферы Земли?", "options": ["Кислород","Азот","CO₂","Аргон"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Цвет неба днём?",             "options": ["Красный","Синий","Зелёный","Чёрный"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Элемент с атомным номером 1?", "options": ["Гелий","Водород","Кислород","Углерод"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Формула скорости?",          "options": ["v=s/t","F=ma","E=mc²","pV=nRT"],  "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Период полураспада урана-235 приблизительно?", "options": ["700 млн лет","700 тыс","70 тыс","7 млн"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Что изучает ботаника?",      "options": ["Растения","Животные","Грибы","Бактерии"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Основная функция митохондрий?", "options": ["Энергия","Ген","Синтез","Деление"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Закон Ома: U = ?",           "options": ["I·R","P·I","Q·ΔT","m·a"],     "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Плотность воды около?",      "options": ["0.1","1","10","100 г/см³"],    "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Энергия фотона E = h·?",     "options": ["c","λ","f","m"],             "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Уравнение Шредингера описывает?", "options": ["Электроны","Волну","Атом","Тепло"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Константа Планка ≈",            "options": ["6.6×10⁻³⁴","6.6×10⁻²⁴","6.6×10⁻⁴","6.6×10⁻¹⁴"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Что такое энтропия?",           "options": ["Энергия","Хаос","Масса","Давление"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Чему равен гравитационный параметр G?", "options": ["6.67×10⁻¹¹","9.81","3×10⁸","1.6×10⁻¹⁹"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Кто сформулировал теорию относительности?", "options": ["Ньютон","Эйнштейн","Галилей","Тесла"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Чему равен pH нейтральной воды?", "options": ["6","7","8","9"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Закон Бойля-Мариотта: PV = ?", "options": ["const","nRT","kE","mgh"], "answer": 0, "points": POINT_TIERS['hard']},
    ],

    "География": [
        {"question": "Столица России?",       "options": ["Москва","Париж","Лондон","Берлин"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Самая длинная река мира?", "options": ["Нил","Амазонка","Янцзы","Миссисипи"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Континент Австралия относится к?", "options": ["Азии","Европе","Океании","Африке"], "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Самая высокая гора —?", "options": ["Эверест","К2","Мак-Кинли","Эльбрус"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Океан между Америкой и Африкой?", "options": ["Индийский","Атлантический","Тихий","Северный"], "answer": 1, "points": POINT_TIERS['easy']},
        {"question": "Пустыня в Африке?",      "options": ["Сахара","Гоби","Калахари","Мохаве"],   "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Столица Франции?",       "options": ["Рим","Берлин","Париж","Мадрид"],      "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Столица Австралии?",     "options": ["Сидней","Мельбурн","Канберра","Перт"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Где находится Марианская впадина?", "options": ["Атлантика","Индийский","Тихий","Северный лед."], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Самое большое озеро мира?", "options": ["Каспийское","Виктория","Танганьика","Мичиган"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Самая длинная гора —?",   "options": ["Анды","Гималаи","Скалы","Альпы"],      "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Где расположен вулкан Килауэа?", "options": ["Исландия","Гавайи","Индонезия","Япония"], "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Страна с наибольшим населением?", "options": ["США","Индия","Китай","Россия"], "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Самая глубокая озеро мира?", "options": ["Байкал","Виктория","Танганьика","Титикака"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Высота Эвереста в метрах?", "options": ["8848","8611","8980","8125"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Самая маленькая страна мира?", "options": ["Монако","Сан-Марино","Ватикан","Лихтенштейн"], "answer": 2, "points": POINT_TIERS['hard']},
        {"question": "По какому меридиану отсчитывают долготу?", "options": ["0°","90°","180°","45°"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Какая река протекает через Каир?", "options": ["Нил","Амазонка","Ганг","Рейн"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Самая высокая вершина России?", "options": ["Эльбрус","Дхаулагири","Казбек","Аннапурна"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Самая длинная река Европы?", "options": ["Волга","Рейн","Днепр","Дунай"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Климатический пояс Москвы?", "options": ["Арктический","Тропический","Умеренный","Субтропический"], "answer": 2, "points": POINT_TIERS['hard']},
    ],

    "Культура": [
        {"question": "Автор 'Евгения Онегина'?",         "options": ["Пушкин","Толстой","Достоевский","Гоголь"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Кто написал 'Войну и мир'?",       "options": ["Пушкин","Гоголь","Толстой","Тургенев"],     "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Жанр романа '1984'?",             "options": ["Антиутопия","Фантастика","Драма","Комедия"], "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Кто создал 'Звездную ночь'?",     "options": ["Ван Гог","Пикассо","Дали","Рембрандт"],     "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Кто написал 'Мастер и Маргарита'?", "options": ["Булгаков","Пушкин","Достоевский","Гоголь"],  "answer": 0, "points": POINT_TIERS['easy']},
        {"question": "Какая страна родина Рембрандта?",   "options": ["Италия","Франция","Нидерланды","Испания"],  "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Жанр балета 'Лебединое озеро'?",   "options": ["Драма","Комедия","Балет","Опера"],         "answer": 2, "points": POINT_TIERS['easy']},
        {"question": "Композитор 'Лунной сонаты'?",      "options": ["Бетховен","Моцарт","Бах","Чайковский"],    "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Режиссер 'Интерстеллара'?",        "options": ["Нолан","Кэмерон","Спилберг","Тарантино"], "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "Автор 'Песни льда и пламени'?",    "options": ["Толкин","Мартин","Роулинг","Кинг"],         "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Первый великий художник Возрождения?", "options": ["Микеланджело","Рафаэль","Боттичелли","Джотто"], "answer": 3, "points": POINT_TIERS['medium']},
        {"question": "Где расположен Колизей?",           "options": ["Париж","Рим","Афины","Иерусалим"],           "answer": 1, "points": POINT_TIERS['medium']},
        {"question": "Автор 'Гамлета'?",                 "options": ["Шекспир","Достоевский","Пушкин","Гоголь"],   "answer": 0, "points": POINT_TIERS['medium']},
        {"question": "На каком языке оригинал 'Илиады'?", "options": ["Латинь","Санскрит","Греческий","Армянский"],  "answer": 2, "points": POINT_TIERS['medium']},
        {"question": "Кто написал 'Божественную комедию'?", "options": ["Данте","Петрарка","Боккаччо","Тассо"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Стиль архитектуры Нотр-Дама?",      "options": ["Готика","Ренессанс","Барокко","Классицизм"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Автор 'Властелина колец'?",         "options": ["Толкин","Мартин","Роулинг","Кинг"],    "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Где впервые поставлен балет 'Щелкунчик'?", "options": ["Париж","Санкт-Петербург","Лондон","Нью-Йорк"], "answer": 1, "points": POINT_TIERS['hard']},
        {"question": "Кто написал 'Сто лет одиночества'?", "options": ["Гарсиа Маркес","Оруэлл","Хемингуэй","Фолкнер"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "Кто создал школу экспрессионизма Дада?", "options": ["Кандинский","Брейгель","Пикассо","Гоген"], "answer": 0, "points": POINT_TIERS['hard']},
        {"question": "В каком веке жил Леонардо да Винчи?",  "options": ["13","14","15","16"],                       "answer": 3, "points": POINT_TIERS['hard']},
    ],
}

INSTRUCTION = (
    "Добро пожаловать в QuizBot!\n"
    "Я задаю вопросы по выбранной сложности и теме.\n"
    "Функции бота:\n"
    "1️⃣ Выберите уровень сложности (легко, средне, сложно).\n"
    "2️⃣ Выберите тему (например, Математика).\n"
    "3️⃣ Ответьте на серию вопросов с 4 вариантами. За каждый правильный ответ вам дается количество очков в зависимости от уровня сложности, а за каждый неправильный в 2 раза меньше отнимается(то есть если за правильный ответ дается 500 очков то за неправильный отнимается 250)\n"
    "4️⃣ Получите итоговый результат и возможность начать заново."
)

def restart_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Перезапустить", callback_data="restart")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INSTRUCTION)
    buttons = [
        [InlineKeyboardButton(f"{lvl.title()} ({pts})", callback_data=f"tier_{lvl}")]
        for lvl, pts in POINT_TIERS.items()
    ]
    await update.message.reply_text(
        "🎚 Выберите сложность:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_TIER

async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(INSTRUCTION)
    buttons = [
        [InlineKeyboardButton(f"{lvl.title()} ({pts})", callback_data=f"tier_{lvl}")]
        for lvl, pts in POINT_TIERS.items()
    ]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🎚 Выберите сложность:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_TIER

async def handle_tier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tier = query.data.split('_')[1]
    context.user_data['points'] = POINT_TIERS[tier]
    buttons = [
        [InlineKeyboardButton(topic, callback_data=f"topic_{topic}")]
        for topic in QUESTIONS.keys()
    ]
    await query.edit_message_text(
        "📚 Выберите тему:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_TOPIC

async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = query.data.split('_', 1)[1]
    context.user_data['topic'] = topic
    all_q = QUESTIONS[topic]
    pts = context.user_data['points']
    filtered = [q for q in all_q if q['points'] == pts]
    random.shuffle(filtered)
    context.user_data['questions'] = filtered[:7]
    context.user_data['current'] = 0
    context.user_data['score'] = 0
    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data['current']
    questions = context.user_data['questions']
    if idx >= len(questions):
        return await finish_game(update, context)
    q = questions[idx]
    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"ans_{i}")]
        for i, opt in enumerate(q['options'])
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"🧠 Вопрос: {q['question']}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply_text(
            f"🧠 Вопрос: {q['question']}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    return ASK_QUESTION

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data['current']
    q = context.user_data['questions'][idx]
    choice = int(query.data.split('_')[1])
    if choice == q['answer']:
        context.user_data['score'] += context.user_data['points']
    context.user_data['current'] += 1
    return await ask_question(update, context)

async def finish_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data['score']
    topic = context.user_data['topic']
    text = f"🏁 Тема: {topic}\nВаш счет: {score} очков"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=restart_keyboard()
    )
    # Сохранение результата
    game_id = str(datetime.datetime.now().timestamp())
    games[game_id] = context.user_data.copy()
    save_game(game_id)
    return GAME_OVER

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception:", exc_info=context.error)
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id:
        await context.bot.send_message(
            chat_id,
            text="⚠️ Произошла ошибка. Перезапустите бота:",
            reply_markup=restart_keyboard()
        )
    return ConversationHandler.END


def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_TIER: [CallbackQueryHandler(handle_tier, pattern='^tier_')],
            SELECT_TOPIC: [CallbackQueryHandler(handle_topic, pattern='^topic_')],
            ASK_QUESTION: [CallbackQueryHandler(handle_answer, pattern='^ans_')],
            GAME_OVER: [CallbackQueryHandler(handle_restart, pattern='^restart$')]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
