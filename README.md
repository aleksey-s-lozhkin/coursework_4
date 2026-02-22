# BriefPost - Сервис email-рассылок

## Описание проекта
BriefPost - это веб-приложение для управления email-рассылками. Сервис позволяет создавать рассылки, управлять клиентами и сообщениями, отслеживать статистику отправок.

## Функциональность

### Для пользователей:
- Регистрация и аутентификация (подтверждение email)
- Управление профилем (редактирование личных данных)
- Создание и управление клиентами (получателями рассылок)
- Создание шаблонов сообщений
- Создание и настройка рассылок
- Просмотр статистики отправок

### Для менеджеров:
- Просмотр всех клиентов и рассылок
- Блокировка пользователей
- Отключение рассылок

## Технологии
- Backend: Django 6.0.2
- База данных: PostgreSQL
- Кеширование: Redis
- Аутентификация: Email + пароль (кастомная модель User)
- Отправка писем: SMTP (Yandex)

## Установка

### 1. Клонировать репозиторий
git clone <url-репозитория>
cd coursework_4

### 2. Установить зависимости
pip install poetry
poetry install

### 3. Настроить переменные окружения
Создайте файл .env на основе .env.example:

# PostgreSQL
DB_NAME=briefpost_db
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Email
EMAIL_HOST_USER=your-email@yandex.by
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@yandex.by

# Redis
CACHE_ENABLE=True
BACKEND=django.core.cache.backends.redis.RedisCache
LOCATION=redis://127.0.0.1:6379/1

### 4. Применить миграции
python manage.py migrate

### 5. Создать группы и права
python manage.py create_groups

### 6. Запустить сервер
python manage.py runserver

## Структура проекта
coursework_4/
├── config/              # Настройки проекта
├── users/               # Приложение пользователей
├── mailings/            # Приложение рассылок
├── clients/             # Приложение клиентов
├── email_messages/      # Приложение сообщений
├── templates/           # HTML шаблоны
├── static/              # Статические файлы
└── manage.py            # Точка входа

## Кастомные команды

### Создание групп менеджеров
python manage.py create_groups

### Отправка запланированных рассылок
### Все активные рассылки
python manage.py send_mailings

### Конкретная рассылка
python manage.py send_mailings --mailing-id 1

### Режим просмотра (без отправки)
python manage.py send_mailings --dry-run

## Права доступа
- Обычный пользователь: управляет только своими данными
- Менеджер: просмотр всех данных, блокировка пользователей
- Администратор: полный доступ

## Системные требования
- Python 3.12+
- PostgreSQL
- Redis (для кеширования)

## Лицензия
© 2025 BriefPost. Все права защищены.