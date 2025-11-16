#!/bin/bash
# Script di deploy per aggiornamenti

set -e

APP_DIR="/opt/talent/app"
VENV_DIR="/opt/talent/app/venv"

echo "🚀 Inizio deploy..."

# Vai nella directory app
cd $APP_DIR

# Pull codice da git
if [ -d ".git" ]; then
    echo "📥 Pull da git..."
    git pull origin main
fi

# Attiva virtual environment
source $VENV_DIR/bin/activate

# Aggiorna dipendenze
echo "📦 Aggiornamento dipendenze..."
pip install -r requirements.txt --upgrade

# Colleziona static files
echo "📁 Raccolta static files..."
python manage.py collectstatic --noinput

# Esegui migrazioni
echo "🗄️ Migrazioni database..."
python manage.py migrate

# Restart services
echo "🔄 Restart servizi..."
sudo supervisorctl restart talent-gunicorn
sudo supervisorctl restart talent-celery
sudo supervisorctl restart talent-celery-beat

echo "✅ Deploy completato!"
