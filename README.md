# Spammer after start — Telegram‑бот для автоматической спам рассылки и админ‑управления

Проект представляет собой Telegram‑бота на Aiogram 3, который:
- Регистрирует пользователя при `/start` и запускает автоматическую периодическую рассылку постов.
- Предоставляет админ‑панель для управления постами, рефералами и статистикой.
- Использует SQLite + SQLAlchemy для БД, Alembic для миграций, Fluent (русские FTL-строки) и APScheduler для фоновых задач.

Ключевые точки:
- Точка входа: `main.py:29–47`
- Инициализация `Bot`, `Dispatcher`, хранилищ, языков и сервисов: `bot/app.py:14–38`
- Сервис рассылки постов: `bot/services/post_manager.py:17–179`
- FTL ресурсы (русский): `bot/utils/fluent_loader.py:7–46`
- Модели БД: `database/models/*.py`
- Обработка ошибок и уведомления: `bot/handlers/other/errors.py:16–101`
- Админ‑команды: `bot/handlers/admin/*.py`
- Юзер‑обработчики: `bot/handlers/user/**/*.py`

---

## Требования к системе

| Компонент | Версия | Назначение |
|---|---:|---|
| Python | 3.10+ | Совместимость с NumPy 2.2, Pydantic v2, Aiogram v3 |
| SQLite | 3.x | Персистентная БД через SQLAlchemy |
| ОС | Windows/Linux/macOS | Кроссплатформенно |

Python‑зависимости (пинованы в `requirements.txt`, основные):
- Aiogram `3.15.0`
- APScheduler `3.11.0`
- SQLAlchemy `2.0.36`, Alembic `1.14.0`

- Fluent Runtime `0.4.0`
- Loguru `0.7.3`
- Pydantic `2.8.2`, Pydantic Settings `2.6.1`
- NumPy `2.2.0`, Matplotlib `3.9.4`
- Прочее: `aiohttp`, `aiosqlite`, `tabulate`, `APScheduler-DI`, `cryptography`, `flyerapi`, `tzlocal`


---

## Установка

1) Клонирование и виртуальное окружение
```bash
git clone <repo-url> spammer_for_start
cd spammer_for_start
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# или source .venv/bin/activate  # Linux/macOS
```

2) Установка зависимостей
```bash
pip install -r requirements.txt
```

4) Настройка переменных окружения (.env)
```bash
copy .env.example .env  # Windows
# или cp .env.example .env  # Linux/macOS
```
Отредактируйте `.env` (см. раздел «Переменные окружения» ниже).

5) Миграции БД (Alembic)
```bash
alembic upgrade head
```

6) Запуск бота
```bash
python main.py
```

---

## Настройка

Пример `.env` (значения приведены в `.env.example`):
```env
BOT__TOKEN="123:ABC"
BOT__USERNAME="example"        # при запуске перезаписывается фактическим username
BOT__SKIP_UPDATES=false        # true -> пропустить накопленные апдейты

DATABASE__DATABASE="database"  # имя файла SQLite без расширения

ADMINS=[123, 456]              # список Telegram user_id админов
HIVIEWS="ABC"                  # токен hiviews (опционально)
INTERVAL=30                    # интервал рассылки (сек) по умолчанию
COUNTER=0                      # счётчик кликов (меняется в рантайме)
ERROR_NOTIFICATION=false       # уведомлять об ошибках разработчику
```

---

## Команды бота


- `/admin` — вход в админ‑панель.
- `/file_id` — получить `file_id` медиа (по реплаю или аргументу).
- `/reset_counter` — сброс `config.counter`.
- `/sql <QUERY>` — выполнить SQL (осторожно!) и вернуть результат.
- `/errors` — список сгруппированных ошибок, просмотр деталей, пометка как «fixed» и переключение уведомлений.

---
