#!/bin/bash

# Script Risoluzione 502 Bad Gateway
# Diagnostica e riavvio servizi Dashboard

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_section() { echo -e "\n${BLUE}═══ $1 ═══${NC}\n"; }

clear
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║        🔧 RISOLUZIONE 502 BAD GATEWAY                    ║
║           Diagnostica e Riavvio Servizi                   ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verifica di essere root
if [ "$EUID" -ne 0 ]; then 
    print_error "Questo script deve essere eseguito come root o con sudo"
    echo ""
    echo "Usa: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/opt/dashboard"
DASHBOARD_USER="dashboard"

print_success "Esecuzione come root - OK"
echo ""

# ============================================
# DIAGNOSTICA INIZIALE
# ============================================
print_section "DIAGNOSTICA INIZIALE"

print_info "Verifica directory progetto..."
if [ -d "$PROJECT_DIR" ]; then
    print_success "Directory $PROJECT_DIR esiste"
else
    print_error "Directory $PROJECT_DIR non trovata!"
    exit 1
fi

print_info "Verifica proprietà file..."
ls -ld $PROJECT_DIR | grep -q $DASHBOARD_USER && print_success "Proprietà corretta" || print_warning "Proprietà da verificare"

print_info "Verifica virtual environment..."
if [ -d "$PROJECT_DIR/venv" ]; then
    print_success "Virtual environment trovato"
else
    print_error "Virtual environment non trovato!"
    exit 1
fi

# ============================================
# ANALISI PROBLEMA 502
# ============================================
print_section "ANALISI PROBLEMA 502"

echo "Un errore 502 Bad Gateway significa che Nginx non riesce a comunicare con Gunicorn."
echo "Le cause più comuni sono:"
echo "  1. Gunicorn non è in esecuzione"
echo "  2. Gunicorn è crashato"
echo "  3. Porta o socket non corretto"
echo "  4. Errori nel codice Python"
echo ""

# ============================================
# VERIFICA GUNICORN
# ============================================
print_section "VERIFICA GUNICORN"

if systemctl list-unit-files | grep -q gunicorn.service; then
    print_success "Servizio Gunicorn configurato"
    
    print_info "Status Gunicorn:"
    if systemctl is-active --quiet gunicorn; then
        print_warning "Gunicorn è attivo MA hai 502 - probabilmente c'è un errore"
    else
        print_error "Gunicorn NON è attivo!"
    fi
    
    echo ""
    systemctl status gunicorn --no-pager -l
else
    print_error "Servizio Gunicorn NON configurato!"
    print_info "Devi creare /etc/systemd/system/gunicorn.service"
fi

echo ""
read -p "Premi INVIO per continuare..."

# ============================================
# VERIFICA ERRORI LOG
# ============================================
print_section "VERIFICA LOG GUNICORN"

print_info "Ultimi 20 errori Gunicorn:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/var/log/dashboard/error.log" ]; then
    tail -n 20 /var/log/dashboard/error.log
else
    print_warning "File log non trovato in /var/log/dashboard/error.log"
    print_info "Provo con journalctl..."
    journalctl -u gunicorn -n 20 --no-pager
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
read -p "Premi INVIO per continuare..."

# ============================================
# TEST DJANGO
# ============================================
print_section "TEST DJANGO"

print_info "Verifica che Django parta senza errori..."

sudo -u $DASHBOARD_USER bash << 'EOF'
cd /opt/dashboard
source venv/bin/activate

echo "Test import Django..."
python -c "import django; print('Django version:', django.get_version())" || exit 1

echo "Test settings..."
python manage.py check --deploy || python manage.py check

echo "Test migrazioni..."
python manage.py migrate --check || echo "⚠ Ci sono migrazioni da applicare"
EOF

if [ $? -eq 0 ]; then
    print_success "Django funziona correttamente"
else
    print_error "Errore in Django - controlla il codice!"
    exit 1
fi

echo ""
read -p "Premi INVIO per continuare con la riparazione..."

# ============================================
# RIPARAZIONE
# ============================================
print_section "RIPARAZIONE AUTOMATICA"

# 1. Imposta permessi corretti
print_info "Step 1/6: Impostazione permessi..."
chown -R $DASHBOARD_USER:$DASHBOARD_USER $PROJECT_DIR
chmod -R 755 $PROJECT_DIR/staticfiles 2>/dev/null || true
print_success "Permessi impostati"

# 2. Crea directory log se non esiste
print_info "Step 2/6: Verifica directory log..."
mkdir -p /var/log/dashboard
chown $DASHBOARD_USER:$DASHBOARD_USER /var/log/dashboard
print_success "Directory log verificata"

# 3. Test Gunicorn manualmente
print_info "Step 3/6: Test Gunicorn manuale..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Avvio Gunicorn per 5 secondi per vedere se ci sono errori..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

timeout 5s sudo -u $DASHBOARD_USER bash << 'EOF' || true
cd /opt/dashboard
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 --workers 3 dashboard_project.wsgi:application
EOF

echo ""
print_warning "Se hai visto errori sopra, quelli sono il problema!"
echo ""
read -p "Hai visto errori? (s/n): " saw_errors

if [ "$saw_errors" = "s" ] || [ "$saw_errors" = "S" ]; then
    print_error "Ci sono errori nel codice Python!"
    print_info "Devi risolvere gli errori mostrati sopra"
    echo ""
    print_info "Errori comuni:"
    echo "  - ModuleNotFoundError: installa il modulo mancante"
    echo "  - ImportError: verifica imports nel codice"
    echo "  - IndentationError: controlla indentazione Python"
    echo ""
    exit 1
fi

# 4. Stop servizi
print_info "Step 4/6: Stop servizi esistenti..."
systemctl stop gunicorn 2>/dev/null || true
killall gunicorn 2>/dev/null || true
print_success "Servizi fermati"

# 5. Verifica configurazione Gunicorn service
print_info "Step 5/6: Verifica configurazione Gunicorn..."

if [ ! -f "/etc/systemd/system/gunicorn.service" ]; then
    print_warning "File gunicorn.service non trovato!"
    print_info "Creazione configurazione Gunicorn..."
    
    cat > /etc/systemd/system/gunicorn.service << 'SERVICEEOF'
[Unit]
Description=Gunicorn daemon for Dashboard Django project
After=network.target

[Service]
Type=notify
User=dashboard
Group=dashboard
WorkingDirectory=/opt/dashboard
Environment="PATH=/opt/dashboard/venv/bin"
ExecStart=/opt/dashboard/venv/bin/gunicorn \
          --workers 3 \
          --bind 127.0.0.1:8000 \
          --access-logfile /var/log/dashboard/access.log \
          --error-logfile /var/log/dashboard/error.log \
          --log-level info \
          dashboard_project.wsgi:application

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
SERVICEEOF
    
    print_success "File gunicorn.service creato"
else
    print_success "File gunicorn.service esiste"
fi

# 6. Riavvia tutto
print_info "Step 6/6: Riavvio servizi..."

print_info "Ricarico systemd..."
systemctl daemon-reload
print_success "Systemd ricaricato"

print_info "Abilito Gunicorn all'avvio..."
systemctl enable gunicorn
print_success "Gunicorn abilitato"

print_info "Avvio Gunicorn..."
systemctl start gunicorn
sleep 3

if systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn avviato correttamente!"
else
    print_error "Gunicorn non è partito!"
    echo ""
    print_info "Vedo gli ultimi log:"
    journalctl -u gunicorn -n 30 --no-pager
    exit 1
fi

print_info "Ricarico Nginx..."
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    print_success "Nginx ricaricato"
else
    print_error "Errore nella configurazione Nginx!"
    print_info "Controlla: nginx -t"
    exit 1
fi

# ============================================
# VERIFICA FINALE
# ============================================
print_section "VERIFICA FINALE"

print_info "Status servizi:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Gunicorn: $(systemctl is-active gunicorn)"
echo "Nginx: $(systemctl is-active nginx)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet gunicorn && systemctl is-active --quiet nginx; then
    print_success "Entrambi i servizi sono attivi!"
else
    print_error "Uno o più servizi non sono attivi!"
fi

# Test connessione locale
print_info "Test connessione locale a Gunicorn..."
if curl -s http://127.0.0.1:8000 > /dev/null 2>&1; then
    print_success "Gunicorn risponde su porta 8000!"
else
    print_error "Gunicorn NON risponde su porta 8000!"
    print_warning "Verifica che sia configurato per porta 8000"
fi

# ============================================
# RISULTATO
# ============================================
print_section "RISULTATO"

SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}         ✓ RIPARAZIONE COMPLETATA!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

print_info "Prova ad accedere a:"
echo "  http://$SERVER_IP"
echo "  http://$SERVER_IP/login/"
echo ""

print_info "Se vedi ancora 502, controlla:"
echo "  1. Log Gunicorn: tail -f /var/log/dashboard/error.log"
echo "  2. Log Nginx: tail -f /var/log/nginx/dashboard_error.log"
echo "  3. Status: systemctl status gunicorn -l"
echo ""

print_info "Comandi utili:"
echo "  # Vedere log in tempo reale"
echo "  journalctl -u gunicorn -f"
echo ""
echo "  # Riavviare manualmente"
echo "  sudo systemctl restart gunicorn"
echo "  sudo systemctl reload nginx"
echo ""
echo "  # Testare Gunicorn direttamente"
echo "  sudo -u dashboard bash"
echo "  cd /opt/dashboard"
echo "  source venv/bin/activate"
echo "  gunicorn --bind 0.0.0.0:8000 dashboard_project.wsgi:application"
echo ""

read -p "Vuoi vedere i log in tempo reale? (s/n): " show_logs

if [ "$show_logs" = "s" ] || [ "$show_logs" = "S" ]; then
    echo ""
    print_info "Mostrando log Gunicorn (CTRL+C per uscire)..."
    echo ""
    journalctl -u gunicorn -f
fi
