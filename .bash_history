pwd
ls -ali
cd /opt/dashboard
ls -ali
bash deploy_auth.sh
ls -ali
exit
ls -ali
bash deploy_auth.sh
ls -ali
ls -ali /scripts
ls -ali scripts
cat scripts/deploy.sh
pwd
pwd
ls -ali
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pwd
cp /opt/dashboard_backup/.env /opt/dashboard/.env
ls -ali
cat .env
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py populate_db
python manage.py runserver 0.0.0.0:8000
ls -ali
deactivate
bash deploy_auth.sh
reboot
exit
source venv/bin/activate
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 dashboard_project.wsgi
deactivate
exit
sudo su - dashboard
pwd
source venv/bin/activate
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from procedures.models import UserProfile

# Crea profili per tutti gli utenti senza profilo
for user in User.objects.all():
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'viewer'}
    )
    if created:
        print(f"✓ Profilo creato per: {user.username}")
EOF

exit
ls -ali
exit
cd /opt/dashboard
pwd
ls -ali
sudo chown -R dashboard:dashboard /opt/dashboard/.gitignore
exit
pwd
ls -ali
exit
