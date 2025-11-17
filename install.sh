#!/bin/bash

################################################################################
# Script di Installazione Automatica - Dashboard Procedure Operative
# Versione: 1.0
# Descrizione: Installa e configura automaticamente l'applicazione Django
#              Dashboard con Nginx, Gunicorn e systemd
################################################################################

set -e  # Esce in caso di errore

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variabili di configurazione
PROJECT_NAME="dashboard"
PROJECT_PATH="/opt/${PROJECT_NAME}"
GIT_REPO="https://github.com/turiliffiu/dashboard_project3.git"
PYTHON_VERSION="3.11"
NGINX_USER="www-data"
SERVER_IP=""

################################################################################
# FUNZIONI HELPER
################################################################################

print_step() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Questo script deve essere eseguito come root"
        echo "Usa: sudo bash install.sh"
        exit 1
    fi
    print_success "Eseguito come root"
}

prompt_continue() {
    echo -e "\n${YELLOW}Vuoi continuare? (s/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[sS]$ ]]; then
        echo "Installazione annullata."
        exit 0
    fi
}

################################################################################
# STEP 1: VERIFICA SISTEMA E RACCOLTA INFO
################################################################################

print_step "STEP 1: VERIFICA SISTEMA E RACCOLTA INFORMAZIONI"

check_root

# Rileva IP del server
SERVER_IP=$(hostname -I | awk '{print $1}')
print_info "IP rilevato: ${SERVER_IP}"

# Chiedi conferma o permetti modifica
echo -e "\n${YELLOW}L'IP del server è corretto? (s per confermare, n per modificare)${NC}"
read -r ip_confirm
if [[ "$ip_confirm" =~ ^[nN]$ ]]; then
    echo "Inserisci l'IP corretto:"
    read -r SERVER_IP
fi

print_success "IP server impostato: ${SERVER_IP}"

# Verifica sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    print_info "Sistema operativo: $NAME $VERSION"
else
    print_error "Sistema operativo non riconosciuto"
    exit 1
fi

prompt_continue

################################################################################
# STEP 2: AGGIORNAMENTO SISTEMA
################################################################################

print_step "STEP 2: AGGIORNAMENTO SISTEMA"

apt update
apt upgrade -y

print_success "Sistema aggiornato"

################################################################################
# STEP 3: INSTALLAZIONE PACCHETTI
################################################################################

print_step "STEP 3: INSTALLAZIONE PACCHETTI NECESSARI"

# Python
print_info "Installazione Python ${PYTHON_VERSION}..."
apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev
apt install -y python3-pip build-essential libpq-dev

# Nginx
print_info "Installazione Nginx..."
apt install -y nginx
systemctl enable nginx

# Redis
print_info "Installazione Redis..."
apt install -y redis-server
systemctl enable redis-server

# Supervisor
print_info "Installazione Supervisor..."
apt install -y supervisor
systemctl enable supervisor

# Git
print_info "Installazione Git..."
apt install -y git

print_success "Tutti i pacchetti installati"

################################################################################
# STEP 4: CREAZIONE UTENTE APPLICATIVO
################################################################################

print_step "STEP 4: CREAZIONE UTENTE APPLICATIVO"

if id "${PROJECT_NAME}" &>/dev/null; then
    print_info "Utente ${PROJECT_NAME} già esistente"
else
    adduser --system --group --home ${PROJECT_PATH} ${PROJECT_NAME}
    usermod -s /bin/bash ${PROJECT_NAME}
    print_success "Utente ${PROJECT_NAME} creato"
fi

mkdir -p ${PROJECT_PATH}
chown ${PROJECT_NAME}:${PROJECT_NAME} ${PROJECT_PATH}

################################################################################
# STEP 5: CLONAZIONE PROGETTO
################################################################################

print_step "STEP 5: CLONAZIONE PROGETTO DA GITHUB"

if [ -d "${PROJECT_PATH}/.git" ]; then
    print_info "Repository già clonato, eseguo pull..."
    cd ${PROJECT_PATH}
    sudo -u ${PROJECT_NAME} git pull
else
    print_info "Clonazione repository..."
    sudo -u ${PROJECT_NAME} git clone ${GIT_REPO} ${PROJECT_PATH}
fi

print_success "Progetto clonato"

################################################################################
# STEP 6: AMBIENTE VIRTUALE E DIPENDENZE
################################################################################

print_step "STEP 6: AMBIENTE VIRTUALE E DIPENDENZE PYTHON"

cd ${PROJECT_PATH}

# Crea virtual environment
if [ ! -d "${PROJECT_PATH}/venv" ]; then
    print_info "Creazione virtual environment..."
    sudo -u ${PROJECT_NAME} python${PYTHON_VERSION} -m venv venv
else
    print_info "Virtual environment già esistente"
fi

# Installa dipendenze
print_info "Installazione dipendenze Python..."
sudo -u ${PROJECT_NAME} bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u ${PROJECT_NAME} bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u ${PROJECT_NAME} bash -c "source venv/bin/activate && pip install gunicorn"

print_success "Dipendenze installate"

################################################################################
# STEP 7: CONFIGURAZIONE DJANGO
################################################################################

print_step "STEP 7: CONFIGURAZIONE DJANGO"

# Genera SECRET_KEY sicura senza dipendere da Django
print_info "Generazione SECRET_KEY..."
SECRET_KEY=$(openssl rand -base64 50 | tr -d "=+/" | cut -c1-50)

# Crea file .env
print_info "Creazione file .env..."
cat > ${PROJECT_PATH}/.env << EOF
DEBUG=False
SECRET_KEY=${SECRET_KEY}
STATIC_ROOT=${PROJECT_PATH}/staticfiles
STATIC_URL=/static/
EOF

chown ${PROJECT_NAME}:${PROJECT_NAME} ${PROJECT_PATH}/.env
chmod 600 ${PROJECT_PATH}/.env

print_success "File .env creato"

# Migrazioni database
print_info "Esecuzione migrazioni database..."
sudo -u ${PROJECT_NAME} bash -c "cd ${PROJECT_PATH} && source venv/bin/activate && python manage.py migrate"

# Collectstatic
print_info "Raccolta file statici..."
sudo -u ${PROJECT_NAME} bash -c "cd ${PROJECT_PATH} && source venv/bin/activate && python manage.py collectstatic --noinput"

# Crea superuser
print_info "Creazione superuser..."
echo -e "\n${YELLOW}Vuoi creare un superuser ora? (s/n)${NC}"
read -r create_super
if [[ "$create_super" =~ ^[sS]$ ]]; then
    sudo -u ${PROJECT_NAME} bash -c "cd ${PROJECT_PATH} && source venv/bin/activate && python manage.py createsuperuser"
fi

# Popola database con esempi
print_info "Popolamento database con esempi..."
sudo -u ${PROJECT_NAME} bash -c "cd ${PROJECT_PATH} && source venv/bin/activate && python manage.py populate_db" || true

print_success "Configurazione Django completata"

################################################################################
# STEP 8: CONFIGURAZIONE PERMESSI (FONDAMENTALE!)
################################################################################

print_step "STEP 8: CONFIGURAZIONE PERMESSI"

print_info "Impostazione permessi directory parent..."
chmod 755 /opt
chmod 755 ${PROJECT_PATH}

print_info "Impostazione permessi file statici..."
chmod -R 755 ${PROJECT_PATH}/staticfiles
chown -R ${PROJECT_NAME}:${PROJECT_NAME} ${PROJECT_PATH}/staticfiles

# Verifica permessi
print_info "Verifica accesso www-data ai file statici..."
if sudo -u ${NGINX_USER} test -r ${PROJECT_PATH}/staticfiles/css/dashboard.css; then
    print_success "Permessi corretti - www-data può leggere i file"
else
    print_error "www-data NON può leggere i file statici!"
    echo "Controlla manualmente i permessi"
fi

################################################################################
# STEP 9: CONFIGURAZIONE NGINX
################################################################################

print_step "STEP 9: CONFIGURAZIONE NGINX"

# Crea file di configurazione Nginx
print_info "Creazione configurazione Nginx..."
cat > /etc/nginx/sites-available/${PROJECT_NAME} << EOF
upstream ${PROJECT_NAME} {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name ${SERVER_IP} ${PROJECT_NAME}.local;
    
    client_max_body_size 10M;
    
    # File statici (CSS, JS, immagini)
    location /static/ {
        alias ${PROJECT_PATH}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Tutte le altre richieste vanno a Gunicorn
    location / {
        proxy_pass http://${PROJECT_NAME};
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeout per richieste lunghe
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
    
    # Log
    access_log /var/log/nginx/${PROJECT_NAME}_access.log;
    error_log /var/log/nginx/${PROJECT_NAME}_error.log;
}
EOF

# Attiva configurazione
print_info "Attivazione configurazione Nginx..."
ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test configurazione
print_info "Test configurazione Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    print_success "Configurazione Nginx valida"
    systemctl restart nginx
    print_success "Nginx riavviato"
else
    print_error "Configurazione Nginx non valida!"
    exit 1
fi

################################################################################
# STEP 10: CONFIGURAZIONE SYSTEMD (GUNICORN)
################################################################################

print_step "STEP 10: CONFIGURAZIONE SYSTEMD PER GUNICORN"

# Crea directory log
mkdir -p /var/log/${PROJECT_NAME}
chown ${PROJECT_NAME}:${PROJECT_NAME} /var/log/${PROJECT_NAME}

# Crea service file
print_info "Creazione service systemd..."
cat > /etc/systemd/system/gunicorn.service << EOF
[Unit]
Description=Gunicorn daemon for Dashboard Django project
After=network.target

[Service]
Type=notify
User=${PROJECT_NAME}
Group=${PROJECT_NAME}
WorkingDirectory=${PROJECT_PATH}
Environment="PATH=${PROJECT_PATH}/venv/bin"
ExecStart=${PROJECT_PATH}/venv/bin/gunicorn \\
          --workers 3 \\
          --bind 127.0.0.1:8000 \\
          --access-logfile /var/log/${PROJECT_NAME}/access.log \\
          --error-logfile /var/log/${PROJECT_NAME}/error.log \\
          dashboard_project.wsgi:application

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Ricarica systemd
print_info "Ricarica configurazione systemd..."
systemctl daemon-reload

# Avvia e abilita servizio
print_info "Avvio servizio Gunicorn..."
systemctl start gunicorn
systemctl enable gunicorn

# Verifica status
sleep 2
if systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn avviato correttamente"
else
    print_error "Gunicorn non è attivo!"
    systemctl status gunicorn
fi

################################################################################
# STEP 11: VERIFICA FINALE
################################################################################

print_step "STEP 11: VERIFICA FINALE DELL'INSTALLAZIONE"

# Verifica servizi
print_info "Verifica servizi attivi..."
services=("nginx" "gunicorn" "redis-server")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        print_success "$service è attivo"
    else
        print_error "$service NON è attivo"
    fi
done

# Test accesso file statici
print_info "Test accesso file statici..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/static/css/dashboard.css | grep -q "200"; then
    print_success "File statici accessibili"
else
    print_error "File statici NON accessibili (verifica permessi)"
fi

################################################################################
# COMPLETAMENTO
################################################################################

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}      🎉 INSTALLAZIONE COMPLETATA CON SUCCESSO! 🎉      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}📋 INFORMAZIONI ACCESSO:${NC}"
echo -e "   URL Dashboard:    ${BLUE}http://${SERVER_IP}${NC}"
echo -e "   URL Admin:        ${BLUE}http://${SERVER_IP}/admin${NC}"
echo -e "   File .env:        ${PROJECT_PATH}/.env"
echo -e "   Log Nginx:        /var/log/nginx/${PROJECT_NAME}_error.log"
echo -e "   Log Gunicorn:     /var/log/${PROJECT_NAME}/error.log"

echo -e "\n${YELLOW}🔧 COMANDI UTILI:${NC}"
echo -e "   Riavvia Gunicorn: ${BLUE}systemctl restart gunicorn${NC}"
echo -e "   Riavvia Nginx:    ${BLUE}systemctl restart nginx${NC}"
echo -e "   Logs Gunicorn:    ${BLUE}journalctl -u gunicorn -f${NC}"
echo -e "   Logs Nginx:       ${BLUE}tail -f /var/log/nginx/${PROJECT_NAME}_error.log${NC}"

if [[ ! "$create_super" =~ ^[sS]$ ]]; then
    echo -e "\n${YELLOW}⚠️  ATTENZIONE: Crea un superuser per accedere all'admin:${NC}"
    echo -e "   ${BLUE}sudo su - ${PROJECT_NAME}${NC}"
    echo -e "   ${BLUE}cd ${PROJECT_PATH}${NC}"
    echo -e "   ${BLUE}source venv/bin/activate${NC}"
    echo -e "   ${BLUE}python manage.py createsuperuser${NC}"
fi

echo -e "\n${GREEN}✅ Apri il browser e vai su: http://${SERVER_IP}${NC}\n"
