# Personal AI Assistant — Telegram Bot

Персональний AI асистент в Telegram. Відповідає на питання, пам'ятає контекст розмови, знає твою базу знань з Google Drive, читає Google Calendar і Gmail. Безкоштовно, працює 24/7.

---

## Що вміє бот

- Відповідає на будь-які питання (Gemini 2.5 Flash / Pro)
- Читає базу знань з Google Drive (папка `my-brain`)
- Показує події з Google Calendar
- Читає і шукає листи в Gmail
- Створює події в Calendar голосом
- Надсилає нагадування за 15 хвилин до зустрічей
- Пам'ятає контекст останніх 10 повідомлень
- Відповідає тією мовою якою пишеш

---

## Що потрібно перед початком

- Акаунт в **Telegram**
- Акаунт на **GitHub** (безкоштовно на github.com)
- Акаунт **Google** (звичайна Gmail пошта)
- Акаунт на **Render** (безкоштовно на render.com)
- Комп'ютер з браузером і Python 3 встановленим

---

## Крок 1 — Створити Telegram бота

1. Відкрий Telegram → знайди **@BotFather** (синя галочка)
2. Натисни **START** → напиши `/newbot`
3. Введи ім'я: `My AI Assistant`
4. Введи username (закінчується на `bot`): `my_ai_assistant_bot`
5. Збережи **токен** вигляду `123456789:ABCdef...`

---

## Крок 2 — Дізнатись свій Telegram ID

1. Знайди в Telegram **@userinfobot**
2. Напиши будь-що
3. Збережи числовий **Id** з відповіді (наприклад `123456789`)

---

## Крок 3 — Отримати Google AI ключ (Gemini)

1. Відкрий **aistudio.google.com** → увійди через Google
2. Натисни **Get API key** → **Create API key**
3. У вікні натисни **"Create API key in new project"** (обов'язково новий проект!)
4. Збережи ключ вигляду `AIzaSy...`

> Новий проект = свіжий безкоштовний ліміт (1500 запитів/день).

---

## Крок 4 — Налаштувати Google OAuth (Calendar, Gmail, Drive)

Це одноразове налаштування для доступу до твоїх Google сервісів.

### 4.1 Google Cloud Console

1. Відкрий **console.cloud.google.com**
2. Вгорі натисни на назву проекту → **New Project**
3. Назви `telegram-assistant` → **Create**
4. Обери новий проект зі списку

### 4.2 Увімкни API

1. Ліве меню → **APIs & Services** → **Library**
2. Знайди і натисни **Enable** для кожного:
   - `Google Drive API`
   - `Google Calendar API`
   - `Gmail API`

### 4.3 OAuth Consent Screen

1. Ліве меню → **APIs & Services** → **OAuth consent screen**
2. Обери **External** → **Create**
3. Заповни:
   - App name: `My Telegram Assistant`
   - User support email: твій Gmail
   - Developer contact: твій Gmail
4. **Save and Continue** на всіх наступних екранах
5. На екрані **Test users** → **Add Users** → введи свій Gmail → **Add**
6. **Save and Continue** → **Back to Dashboard**

### 4.4 Створи OAuth Credentials

1. Ліве меню → **APIs & Services** → **Credentials**
2. **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `telegram-bot-client` → **Create**
5. Натисни **Download JSON** — збережи файл

### 4.5 Отримай Refresh Token

Встанови бібліотеку (один раз):
```bash
pip3 install google-auth-oauthlib --break-system-packages
```

Запусти скрипт авторизації:
```bash
python3 get_token.py
```

Відкриється браузер → увійди в Google → натисни **Allow**.

> Якщо Google показує "App not verified" → натисни **Advanced** → **Go to telegram-assistant (unsafe)** — це нормально.

У терміналі з'явиться:
```
GOOGLE_REFRESH_TOKEN=1//03...
```
Збережи цей токен.

---

## Крок 5 — Налаштувати базу знань в Google Drive

1. Відкрий Google Drive
2. Знайди папку **my-brain** (бот створить її автоматично при першому запуску)
3. Клади туди MD файли зі своїми нотатками
4. Бот автоматично шукає по ним при відповідях

> Файли можна редагувати прямо в Google Drive з телефону або комп'ютера.

---

## Крок 6 — Скопіювати проект і задеплоїти

### 6.1 Fork на GitHub

1. Відкрий **github.com/igor-shulga/telegram-ai-assistant**
2. Натисни **Fork** → **Create fork**

### 6.2 Зареєструватись на Render

1. Відкрий **render.com** → **Sign up with GitHub**

### 6.3 Створити Web Service

1. **New +** → **Web Service**
2. Обери своє fork репо
3. Налаштування:
   - Region: `Frankfurt (EU Central)`
   - Runtime: `Docker`
   - Instance Type: `Free`
4. **Create Web Service**
5. Зачекай 3-5 хвилин — збережи URL сервісу (наприклад `https://my-assistant-xyz.onrender.com`)

---

## Крок 7 — Додати змінні середовища в Render

**Environment → Add Variable** — додай всі 7:

| Key | Value | Звідки |
|-----|-------|--------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC...` | Крок 1 |
| `GOOGLE_API_KEY` | `AIzaSy...` | Крок 3 |
| `WEBHOOK_BASE_URL` | `https://your-app.onrender.com` | Крок 6 — URL Render |
| `ALLOWED_USER_ID` | `123456789` | Крок 2 |
| `GOOGLE_REFRESH_TOKEN` | `1//03...` | Крок 4.5 |
| `GOOGLE_CLIENT_ID` | `525...apps.googleusercontent.com` | З JSON файлу (Крок 4.4) |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | З JSON файлу (Крок 4.4) |

**Save, rebuild, and deploy**

---

## Крок 8 — Перший тест

1. Відкрий Telegram → знайди свого бота → `/start`
2. Напиши `/today` — має показати події з Calendar
3. Напиши `/inbox` — непрочитані листи з Gmail
4. Запитай щось про фасилітацію

---

## Команди

| Команда | Що робить |
|---------|-----------|
| `/start` | Привітання |
| `/clear` | Очистити пам'ять розмови |
| `/today` | Події на сьогодні |
| `/inbox` | Непрочитані листи |

## Приклади запитів

```
"Що у мене завтра?"                          → Calendar на 3 дні
"Створи зустріч в четвер о 15:00"            → Нова подія в Calendar
"Знайди листи від Токарського за тиждень"    → Gmail пошук
"Яку техніку для групи 40 людей?"            → База знань з Drive
"Порассуждай детально про цю проблему"       → Перемикання на Gemini Pro
```

---

## Режим глибокого аналізу

Додай до повідомлення одне з цих слів для Gemini Pro:

`подумай` / `порассуждай` / `розмірковуй` / `think deeply` / `детально` / `подробно`

---

## Нагадування

Бот автоматично надсилає нагадування за 15 хвилин до кожної події в Calendar. Нічого налаштовувати не потрібно.

---

## Важливо знати

- Render free tier "засинає" через 15 хвилин без повідомлень. Перше повідомлення після сну ~30-50 секунд.
- Безкоштовний ліміт Gemini: 1500 запитів/день. Для особистого використання більш ніж достатньо.
- Пам'ять розмови зберігається в межах сесії. `/clear` очищає вручну.

---

## Стек

- **Bot:** aiogram v3 (webhook), FastAPI, Python 3.12
- **LLM:** Google Gemini 2.5 Flash / Pro
- **Google:** Calendar API, Gmail API, Drive API (OAuth2)
- **Hosting:** Render (Docker, free tier)
- **Cost:** $0/month
