#!/bin/bash
set -e
echo "=== Деплой на сервер ==="

SERVER="ubuntu@216.250.9.226"
REMOTE="/home/ubuntu/webmenu"
LOCAL="/home/sk/webmenu"

# Синхронизируем весь репозиторий, а не отдельные файлы вручную — раньше
# список scp отставал от кода (например, menu/middleware.py вообще не
# попадал на сервер) и это не было заметно, пока что-то не ломалось.
# Без --delete: не трогаем то, что есть только на сервере (.env с прод-
# секретами, media/, releases/app/ с APK и т.п.) — но и не подчищаем
# файлы, удалённые локально, их придётся убирать на сервере руками.
rsync -avz \
  --exclude='.git/' \
  --exclude='venv/' \
  --exclude='.venv/' \
  --exclude='env/' \
  --exclude='ENV/' \
  --exclude='__pycache__/' \
  --exclude='*.py[cod]' \
  --exclude='.env' \
  --exclude='.env.local' \
  --exclude='.env.*.local' \
  --exclude='db.sqlite3' \
  --exclude='staticfiles/' \
  --exclude='media/' \
  --exclude='releases/' \
  --exclude='.ruff_cache/' \
  --exclude='.claude/' \
  "$LOCAL"/ "$SERVER:$REMOTE"/

# Команды на сервере
ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/webmenu
source venv/bin/activate
pip install -r requirements.txt --quiet
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
echo "=== Готово ==="
ENDSSH
