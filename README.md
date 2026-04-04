# Speed Recruiting Bot

Telegram-бот для автоматичної генерації розкладів заходів швидкого рекрутингу.

## Концепція

Студенти заходять до кімнати **сесіями** (до K осіб за раз). Усередині кожної сесії проводяться M раундів — кожен студент відвідує M різних партнерів. Кількість сесій розраховується автоматично: `⌈N / K⌉`.

```text
/generate N K M

N — загальна кількість студентів (1–1000)
K — кількість партнерів у кімнаті  (1–200)
M — кількість раундів за сесію     (1–50, M ≤ K)
```

## Локальна розробка

### 1. Вимоги

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) або `pip`
- Токен бота від [@BotFather](https://t.me/BotFather)

### 2. Клонування та встановлення залежностей

```bash
git clone https://github.com/Maximax67/speed-recruiting-bot
cd speed-recruiting-bot

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Змінні середовища

Створіть файл `.env` у корені проєкту:

```dotenv
BOT_TOKEN=1234567890:AAF...your_token_here

# Для локальної розробки нічого більше не потрібно.
# ENV за замовчуванням = "development" → запускається polling.
```

### 4. Запуск

```bash
python main.py
```

У режимі `development` бот використовує **long polling** — вебхук не потрібен. Бот одразу готовий до роботи в Telegram.
