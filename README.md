# Webmenu

Веб-меню для кофейни. Django 5.2 + PostgreSQL, мультиязычность (ru/en/tk).

## Стек

- Python 3.12+
- Django 5.2
- PostgreSQL 14+
- gunicorn (prod)
- nginx (prod, отдача static/media)

## Локальный запуск

### 1. Клонировать и создать venv

```bash
git clone <repo-url> webmenu
cd webmenu
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Настроить окружение

```bash
cp .env.example .env
# Сгенерировать SECRET_KEY и вставить в .env:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Отредактировать `.env`: поставить свой `SECRET_KEY` и `DATABASE_URL`.

### 3. Поднять базу

Создать БД в Postgres:

```bash
sudo -u postgres psql -c "CREATE USER webmenu WITH PASSWORD 'webmenu';"
sudo -u postgres psql -c "CREATE DATABASE webmenu OWNER webmenu;"
```

### 4. Миграции и админка

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Открыть http://localhost:8000

## Деплой

См. `docs/deploy.md` (будет добавлено).

## Структура

```
config/         — настройки проекта
menu/           — основное приложение
templates/      — HTML-шаблоны
static/         — CSS/JS/изображения (отдаётся nginx в проде)
media/          — загруженные через админку картинки
```