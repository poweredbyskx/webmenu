#!/bin/bash
echo "=== Деплой на сервер ==="

SERVER="ubuntu@216.250.9.226"
REMOTE="/home/ubuntu/webmenu"
LOCAL="/home/sk/webmenu"

# Только код — без медиа, без .pyc
scp $LOCAL/menu/models.py $SERVER:$REMOTE/menu/
scp $LOCAL/menu/views.py $SERVER:$REMOTE/menu/
scp $LOCAL/menu/admin.py $SERVER:$REMOTE/menu/
scp $LOCAL/menu/urls.py $SERVER:$REMOTE/menu/
scp $LOCAL/menu/sitemaps.py $SERVER:$REMOTE/menu/
scp $LOCAL/menu/context_processors.py $SERVER:$REMOTE/menu/
scp -r $LOCAL/menu/migrations/ $SERVER:$REMOTE/menu/
scp -r $LOCAL/templates/ $SERVER:$REMOTE/
scp $LOCAL/static/menu/css/style.css $SERVER:$REMOTE/static/menu/css/
scp $LOCAL/static/menu/css/theme.css $SERVER:$REMOTE/static/menu/css/
scp $LOCAL/requirements.txt $SERVER:$REMOTE/

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
