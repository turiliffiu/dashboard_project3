#!/bin/bash

# Script Diagnosi e Risoluzione Errore 500 Post-Login

echo "🔍 Diagnostica Errore 500 Post-Login"
echo "====================================="
echo ""

# Verifica root
if [ "$EUID" -ne 0 ]; then 
    echo "Esegui come root: sudo bash $0"
    exit 1
fi

echo "📋 Cerco errori recenti nei log..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Log Gunicorn
if [ -f "/var/log/dashboard/error.log" ]; then
    echo "Ultimi errori da /var/log/dashboard/error.log:"
    tail -n 100 /var/log/dashboard/error.log | grep -A 20 "Error\|Exception\|Traceback" | tail -40
else
    echo "Ultimi errori da journalctl:"
    journalctl -u gunicorn -n 100 | grep -A 20 "Error\|Exception\|Traceback" | tail -40
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🧪 Test Django manuale..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test Django
sudo -u dashboard bash << 'EOF'
cd /opt/dashboard
source venv/bin/activate

echo "Test import base..."
python -c "import django; django.setup()"

echo "Test import procedures..."
python -c "from procedures.models import UserProfile, ProcedureCategory"

echo "Test check Django..."
python manage.py check

echo "Test shell per vedere se ci sono errori..."
python manage.py shell << 'PYEOF'
from django.contrib.auth.models import User
from procedures.models import UserProfile, ProcedureCategory

# Conta oggetti
print(f"Utenti totali: {User.objects.count()}")
print(f"Profili totali: {UserProfile.objects.count()}")
print(f"Categorie totali: {ProcedureCategory.objects.count()}")

# Verifica che tutti gli utenti abbiano un profilo
users_without_profile = []
for user in User.objects.all():
    if not hasattr(user, 'profile'):
        users_without_profile.append(user.username)
        print(f"PROBLEMA: Utente {user.username} NON ha profilo!")

if not users_without_profile:
    print("✓ Tutti gli utenti hanno un profilo")
else:
    print(f"✗ {len(users_without_profile)} utenti senza profilo!")
PYEOF
EOF

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Vuoi applicare le correzioni automatiche? (s/n): " apply_fix

if [ "$apply_fix" != "s" ] && [ "$apply_fix" != "S" ]; then
    echo "Ok, nessuna modifica applicata."
    exit 0
fi

echo ""
echo "🔧 Applicazione correzioni..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Assicura che tutti gli utenti abbiano un profilo
echo "1. Verifica profili utenti..."
sudo -u dashboard bash << 'EOF'
cd /opt/dashboard
source venv/bin/activate

python manage.py shell << 'PYEOF'
from django.contrib.auth.models import User
from procedures.models import UserProfile

created_count = 0
for user in User.objects.all():
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'viewer'}
    )
    if created:
        created_count += 1
        print(f"✓ Profilo creato per: {user.username}")

if created_count == 0:
    print("✓ Tutti gli utenti hanno già un profilo")
else:
    print(f"✓ Creati {created_count} nuovi profili")
PYEOF
EOF

echo ""

# 2. Verifica vista dashboard
echo "2. Verifica vista dashboard..."

VIEWS_FILE="/opt/dashboard/procedures/views.py"

# Backup
cp $VIEWS_FILE ${VIEWS_FILE}.backup.login
echo "✓ Backup views.py creato"

# Verifica che la vista dashboard abbia il decorator @login_required
if grep -A 1 "def dashboard(request):" $VIEWS_FILE | grep -q "@login_required"; then
    echo "✓ Decorator @login_required presente"
else
    echo "⚠ Decorator @login_required potrebbe mancare"
fi

echo ""

# 3. Verifica settings.py
echo "3. Verifica configurazione settings.py..."

SETTINGS_FILE="/opt/dashboard/dashboard_project/settings.py"

echo "Verifica LOGIN_REDIRECT_URL..."
if grep -q "LOGIN_REDIRECT_URL.*=.*['\"]procedures:dashboard['\"]" $SETTINGS_FILE; then
    echo "✓ LOGIN_REDIRECT_URL corretto"
else
    echo "⚠ LOGIN_REDIRECT_URL da verificare"
    grep "LOGIN_REDIRECT_URL" $SETTINGS_FILE || echo "  (non trovato)"
fi

echo ""

# 4. Test accesso alla vista dashboard direttamente
echo "4. Test vista dashboard..."
sudo -u dashboard bash << 'EOF'
cd /opt/dashboard
source venv/bin/activate

python manage.py shell << 'PYEOF'
from django.test import RequestFactory
from django.contrib.auth.models import User
from procedures.views import dashboard

# Crea request factory
factory = RequestFactory()

# Prendi un utente
try:
    user = User.objects.first()
    if user:
        request = factory.get('/')
        request.user = user
        
        # Prova a chiamare la vista
        try:
            response = dashboard(request)
            print(f"✓ Vista dashboard risponde: {response.status_code}")
        except Exception as e:
            print(f"✗ Errore nella vista dashboard: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠ Nessun utente nel database")
except Exception as e:
    print(f"✗ Errore test: {e}")
PYEOF
EOF

echo ""

# 5. Riavvia Gunicorn
echo "5. Riavvio Gunicorn..."
systemctl restart gunicorn
sleep 3

if systemctl is-active --quiet gunicorn; then
    echo "✓ Gunicorn riavviato"
else
    echo "✗ Errore riavvio Gunicorn!"
    journalctl -u gunicorn -n 20
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Correzioni applicate!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🧪 Test finale..."
echo ""
echo "Ora prova:"
echo "  1. Vai su http://TUO_IP/login/"
echo "  2. Fai login"
echo "  3. Dovresti vedere la dashboard"
echo ""
echo "Se vedi ancora errore 500, esegui:"
echo "  sudo journalctl -u gunicorn -f"
echo ""
echo "E fai login in un'altra finestra per vedere l'errore esatto."
echo ""
