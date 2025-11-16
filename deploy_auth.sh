#!/bin/bash

# Script di Deploy per Sistema Autenticazione
# Dashboard Procedure Operative
# Versione: 1.0

set -e  # Exit on error

echo "🚀 Inizio deployment sistema autenticazione..."
echo ""

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funzione per stampare messaggi colorati
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Verifica di essere nella directory corretta
if [ ! -f "manage.py" ]; then
    print_error "Errore: manage.py non trovato!"
    print_info "Assicurati di essere nella directory del progetto Django"
    exit 1
fi

print_success "Directory progetto verificata"

# Attiva virtual environment se esiste
if [ -d "venv" ]; then
    print_info "Attivazione virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment attivato"
else
    print_warning "Virtual environment non trovato, continuo senza..."
fi

# 1. Backup database
print_info "Step 1/7: Backup database..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"
    print_success "Backup database creato"
else
    print_warning "Database non trovato (prima installazione?)"
fi

# 2. Verifica dipendenze
print_info "Step 2/7: Verifica dipendenze..."
pip list | grep -q Django || {
    print_error "Django non installato!"
    exit 1
}
print_success "Dipendenze verificate"

# 3. Applica migrazioni
print_info "Step 3/7: Applicazione migrazioni..."
python manage.py makemigrations
python manage.py migrate
print_success "Migrazioni applicate con successo"

# 4. Crea profili per utenti esistenti
print_info "Step 4/7: Creazione profili per utenti esistenti..."
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from procedures.models import UserProfile

users_updated = 0
for user in User.objects.all():
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'viewer'}
    )
    if created:
        users_updated += 1
        print(f"Profilo creato per: {user.username}")

if users_updated > 0:
    print(f"Creati {users_updated} profili utente")
else:
    print("Tutti gli utenti hanno già un profilo")
EOF
print_success "Profili utente verificati"

# 5. Chiedi se creare un admin
print_info "Step 5/7: Creazione amministratore..."
read -p "Vuoi creare un nuovo utente amministratore? (s/n): " create_admin

if [ "$create_admin" = "s" ] || [ "$create_admin" = "S" ]; then
    read -p "Username admin: " admin_username
    read -sp "Password admin: " admin_password
    echo ""
    
    python manage.py create_user "$admin_username" \
        --password "$admin_password" \
        --role admin \
        --email "admin@dashboard.local" 2>/dev/null && \
        print_success "Amministratore '$admin_username' creato con successo" || \
        print_warning "Errore nella creazione dell'admin (potrebbe già esistere)"
else
    print_info "Creazione admin saltata"
fi

# 6. Raccolta file statici
print_info "Step 6/7: Raccolta file statici..."
python manage.py collectstatic --noinput
print_success "File statici raccolti"

# 7. Riavvio servizi
print_info "Step 7/7: Riavvio servizi..."

# Verifica se gunicorn è attivo come servizio
if systemctl is-active --quiet gunicorn 2>/dev/null; then
    print_info "Riavvio Gunicorn..."
    sudo systemctl restart gunicorn
    print_success "Gunicorn riavviato"
else
    print_warning "Servizio Gunicorn non trovato (deployment manuale?)"
fi

# Verifica nginx
if systemctl is-active --quiet nginx 2>/dev/null; then
    print_info "Ricaricamento Nginx..."
    sudo nginx -t && sudo systemctl reload nginx
    print_success "Nginx ricaricato"
else
    print_warning "Nginx non trovato o non attivo"
fi

echo ""
echo "============================================"
print_success "🎉 DEPLOYMENT COMPLETATO CON SUCCESSO! 🎉"
echo "============================================"
echo ""
print_info "📋 Riepilogo:"
echo "  - Database migrato"
echo "  - Profili utente creati/verificati"
echo "  - File statici raccolti"
echo "  - Servizi riavviati"
echo ""
print_info "🔗 Prossimi passi:"
echo "  1. Accedi al sito: http://$(hostname -I | awk '{print $1}')"
echo "  2. Fai login con le tue credenziali"
echo "  3. Vai su 'Gestione Utenti' per gestire ruoli"
echo ""
print_info "📚 Documentazione:"
echo "  - Leggi GUIDA_AUTENTICAZIONE.md per dettagli"
echo "  - Leggi RIEPILOGO_MODIFICHE.md per vedere tutte le modifiche"
echo ""

# Mostra status finale
print_info "Status servizi:"
if systemctl is-active --quiet gunicorn 2>/dev/null; then
    echo "  Gunicorn: $(systemctl is-active gunicorn)"
else
    echo "  Gunicorn: non configurato"
fi

if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "  Nginx: $(systemctl is-active nginx)"
else
    echo "  Nginx: non configurato"
fi

echo ""
print_success "Buon lavoro con la tua Dashboard! 🚀"
