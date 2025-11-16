#!/bin/bash

# Script Rapido Riavvio Servizi Dashboard
# Usa questo se hai già fatto tutto e vuoi solo riavviare

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 Riavvio Servizi Dashboard${NC}"
echo ""

# Verifica root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Devi essere root! Usa: sudo bash $0${NC}"
    exit 1
fi

# 1. Imposta permessi
echo "📁 Impostazione permessi..."
chown -R dashboard:dashboard /opt/dashboard
chmod -R 755 /opt/dashboard/staticfiles 2>/dev/null || true
echo -e "${GREEN}✓ Permessi OK${NC}"

# 2. Crea directory log
echo "📝 Verifica directory log..."
mkdir -p /var/log/dashboard
chown dashboard:dashboard /var/log/dashboard
echo -e "${GREEN}✓ Log directory OK${NC}"

# 3. Ricarica systemd
echo "⚙️  Ricaricamento systemd..."
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd ricaricato${NC}"

# 4. Stop Gunicorn
echo "🛑 Stop Gunicorn..."
systemctl stop gunicorn 2>/dev/null || true
killall gunicorn 2>/dev/null || true
sleep 1
echo -e "${GREEN}✓ Gunicorn fermato${NC}"

# 5. Start Gunicorn
echo "🚀 Avvio Gunicorn..."
systemctl enable gunicorn
systemctl start gunicorn
sleep 3

if systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✓ Gunicorn avviato!${NC}"
else
    echo -e "${RED}✗ Gunicorn non è partito!${NC}"
    echo "Vedo gli ultimi errori:"
    journalctl -u gunicorn -n 20 --no-pager
    exit 1
fi

# 6. Test Nginx e reload
echo "🌐 Ricaricamento Nginx..."
nginx -t 2>&1
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo -e "${GREEN}✓ Nginx ricaricato${NC}"
else
    echo -e "${RED}✗ Errore configurazione Nginx${NC}"
    exit 1
fi

# Status finale
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Status Servizi:"
echo "  Gunicorn: $(systemctl is-active gunicorn)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet gunicorn && systemctl is-active --quiet nginx; then
    echo ""
    echo -e "${GREEN}✅ TUTTO OK!${NC}"
    echo ""
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "Accedi a: http://$SERVER_IP"
else
    echo ""
    echo -e "${RED}⚠️  Problema con i servizi!${NC}"
    echo ""
    echo "Comandi diagnostica:"
    echo "  journalctl -u gunicorn -n 50"
    echo "  tail -f /var/log/dashboard/error.log"
fi

echo ""
