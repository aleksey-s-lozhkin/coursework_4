# BriefPost — сервис email‑рассылок

## Описание проекта

BriefPost — веб‑приложение для управления email‑рассылками. Сервис позволяет создавать рассылки, управлять списками получателей и сообщениями, а также отслеживать статистику отправок.

## Функциональность

### Возможности для пользователей

- регистрация и аутентификация (с подтверждением email);
- управление личным профилем (редактирование данных);
- работа с клиентами (получателями рассылок): создание и управление списками;
- создание шаблонов сообщений;
- настройка и запуск рассылок;
- просмотр статистики отправок.

### Возможности для менеджеров

- просмотр всех клиентов и рассылок в системе;
- блокировка пользователей;
- отключение рассылок.

## Технологический стек

- **Backend:** Django 6.0.2;
- **База данных:** PostgreSQL;
- **Кеширование:** Redis;
- **Аутентификация:** email + пароль (кастомная модель User);
- **Отправка писем:** SMTP (Yandex).

## Инструкция по установке

### Шаг 1. Клонирование репозитория

```
git clone <url-репозитория>
cd coursework_4
```

### Шаг 2. Установка зависимостей
```
pip install poetry
poetry install
```
### Шаг 3. Настройка переменных окружения
Создайте файл .env на основе шаблона .env.example со следующими параметрами:
```aiignore
# PostgreSQL
DB_NAME=briefpost_db
DB_USER=postgres
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
```
### Шаг 4. Применение миграций
```aiignore
python manage.py migrate
```
### Шаг 5. Создание superuser, групп и прав доступа
```aiignore
#Создание superuser
python manage.py createadmin

#Создание груп
python manage.py create_groups
```
### Шаг 6. Запуск сервера
```aiignore
python manage.py runserver
```
## Структура проекта
```
coursework_4/
├── config/               # Настройки проекта
├── users/                # Приложение пользователей
├── mailings/             # Приложение рассылок
├── clients/              # Приложение клиентов
├── email_messages/       # Приложение сообщений
├── templates/            # HTML‑шаблоны
├── static/               # Статические файлы
└── manage.py             # Точка входа
```
## Кастомные команды управления
```aiignore
Отправка запланированных рассылок:

Для всех активных рассылок:
python manage.py send_mailings

Для конкретной рассылки (по ID):
python manage.py send_mailings --mailing-id 1

Режим просмотра (без фактической отправки):
python manage.py send_mailings --dry-run
```
## Права доступа
- Обычный пользователь: может управлять только своими данными и рассылками.

- Менеджер: имеет доступ к просмотру всех данных в системе, может блокировать пользователей и отключать рассылки.

- Администратор: обладает полным доступом ко всем функциям системы.
## Системные требования
- Python 3.12+;

- PostgreSQL;

- Redis.
## Лицензия
© 2026 BriefPost. Все права защищены.