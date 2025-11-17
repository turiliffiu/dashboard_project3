# 🚀 GUIDA RAPIDA - Script Installazione Automatica Dashboard

## 📋 Prerequisiti

- Server Ubuntu 20.04 / 22.04 / 24.04
- Accesso root o sudo
- Connessione Internet

### Crea un Container Ubuntu:
     
      - arch: amd64
      - cores: 1
      - features: nesting=1
      - hostname: dashboard
      - memory: 2048
      - net0: name=eth0,bridge=vmbr0,firewall=1,ip=dhcp
      - ostype: ubuntu
      - rootfs: local-lvm,size=20G
      - swap: 2048
      - unprivileged: 1

Sulla shell del nuovo Container su Proxmox:

`sudo nano /etc/ssh/sshd_config` <br>

Modificare i seguneti parametri:

     PermitRootLogin yes
     PasswordAuthentication yes
     PermitEmptyPasswords no

---

## 🎯 INSTALLAZIONE IN 3 PASSI

### 1️⃣ Scarica lo script

```bash
# Opzione A: Scarica direttamente (se disponibile online)
wget https://raw.githubusercontent.com/turiliffiu/dashboard_project3/main/install.sh

# Opzione B: Crea manualmente il file
nano install.sh
# (copia e incolla il contenuto dello script)
```

### 2️⃣ Rendi eseguibile

```bash
chmod +x install.sh
```

### 3️⃣ Esegui come root

```bash
sudo bash install.sh
```

---

## 🔄 COSA FA LO SCRIPT

Lo script esegue automaticamente tutti i passaggi del README:

### ✅ STEP 1: Verifica Sistema
- Controlla che sei root
- Rileva automaticamente l'IP del server
- Ti chiede conferma prima di procedere

### ✅ STEP 2: Aggiornamento Sistema
- `apt update`
- `apt upgrade -y`

### ✅ STEP 3: Installazione Pacchetti
- Python 3.11
- Nginx
- Redis
- Supervisor
- Git

### ✅ STEP 4: Creazione Utente
- Crea utente `dashboard`
- Configura home in `/opt/dashboard`

### ✅ STEP 5: Clonazione Progetto
- Clona da GitHub automaticamente

### ✅ STEP 6: Ambiente Virtuale
- Crea virtual environment
- Installa tutte le dipendenze Python
- Installa Gunicorn

### ✅ STEP 7: Configurazione Django
- **Genera automaticamente SECRET_KEY sicura**
- Crea file `.env` con configurazioni corrette
- Esegue `migrate`
- Esegue `collectstatic`
- Ti chiede se vuoi creare superuser
- Popola database con esempi

### ✅ STEP 8: Permessi (FONDAMENTALE!)
- Imposta `chmod 755` su `/opt` e `/opt/dashboard`
- Imposta `chmod -R 755` su `staticfiles`
- **Verifica** che `www-data` possa leggere i file

### ✅ STEP 9: Configurazione Nginx
- Crea configurazione con IP rilevato automaticamente
- Attiva il sito
- Disattiva sito default
- Testa configurazione con `nginx -t`
- Riavvia Nginx

### ✅ STEP 10: Systemd (Gunicorn)
- Crea service systemd
- Avvia Gunicorn automaticamente
- Abilita autostart al boot

### ✅ STEP 11: Verifica Finale
- Controlla che tutti i servizi siano attivi
- Testa accesso ai file statici
- Mostra riepilogo con URL e comandi utili

---

## 🎬 ESEMPIO OUTPUT

```
═══════════════════════════════════════════════════════
STEP 1: VERIFICA SISTEMA E RACCOLTA INFORMAZIONI
═══════════════════════════════════════════════════════

✅ Eseguito come root
ℹ️  IP rilevato: 192.168.1.188

L'IP del server è corretto? (s per confermare, n per modificare)
s
✅ IP server impostato: 192.168.1.188
...
```

---

## 📝 DOPO L'INSTALLAZIONE

### Accedi alla Dashboard
```
http://TUO_IP_SERVER
```

### Crea Superuser (se non fatto durante installazione)
```bash
sudo su - dashboard
cd /opt/dashboard
source venv/bin/activate
python manage.py createsuperuser
```

### Accedi all'Admin
```
http://TUO_IP_SERVER/admin
```

---

## 🔧 COMANDI UTILI

### Riavvia Servizi
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Visualizza Log
```bash
# Log Gunicorn in tempo reale
sudo journalctl -u gunicorn -f

# Log Nginx errori
sudo tail -f /var/log/nginx/dashboard_error.log

# Log Nginx accessi
sudo tail -f /var/log/nginx/dashboard_access.log
```

### Status Servizi
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status redis-server
```

### Aggiorna Progetto
```bash
sudo su - dashboard
cd /opt/dashboard
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
exit

# Riavvia Gunicorn
sudo systemctl restart gunicorn
```

---

## 🛠️ RISOLUZIONE PROBLEMI

### Problema: Script si interrompe

**Causa:** Errore in uno step precedente

**Soluzione:**
```bash
# Visualizza errore specifico
# Lo script mostra sempre cosa è andato storto

# Puoi rieseguire lo script
sudo bash install.sh
# Lo script rileverà cosa è già installato e continuerà
```

### Problema: Gunicorn non parte

**Verifica log:**
```bash
sudo journalctl -u gunicorn -n 50
```

**Possibili cause:**
- File `.env` mancante o errato
- Virtual environment non creato correttamente
- Porta 8000 già in uso

### Problema: 403 Forbidden sui file statici

**Verifica permessi:**
```bash
ls -la /opt/dashboard/staticfiles/css/
sudo -u www-data cat /opt/dashboard/staticfiles/css/dashboard.css
```

**Correggi manualmente:**
```bash
sudo chmod 755 /opt
sudo chmod 755 /opt/dashboard
sudo chmod -R 755 /opt/dashboard/staticfiles
sudo systemctl restart nginx
```

### Problema: Nginx non parte

**Test configurazione:**
```bash
sudo nginx -t
```

**Visualizza errori:**
```bash
sudo tail -f /var/log/nginx/error.log
```

---

## 🔒 SICUREZZA

### File .env

Lo script genera automaticamente una SECRET_KEY sicura, ma verifica sempre:

```bash
sudo cat /opt/dashboard/.env
```

Dovrebbe contenere:
```
DEBUG=False
SECRET_KEY=una_chiave_lunga_e_casuale_generata_automaticamente
STATIC_ROOT=/opt/dashboard/staticfiles
STATIC_URL=/static/
```

### Permessi File Sensibili

```bash
# .env deve essere leggibile solo da dashboard
sudo chmod 600 /opt/dashboard/.env
sudo chown dashboard:dashboard /opt/dashboard/.env

# Database deve essere protetto
sudo chmod 600 /opt/dashboard/db.sqlite3
sudo chown dashboard:dashboard /opt/dashboard/db.sqlite3
```

---

## 📊 STRUTTURA FILE DOPO INSTALLAZIONE

```
/opt/dashboard/
├── venv/                    # Virtual environment Python
├── dashboard_project/       # Configurazione Django
├── procedures/              # App principale
├── procedure_files/         # File .txt procedure
├── staticfiles/            # File statici (CSS, JS)
├── db.sqlite3              # Database SQLite
├── .env                    # Configurazioni (SECRET_KEY, DEBUG, ecc.)
├── manage.py
└── requirements.txt

/etc/nginx/sites-available/
└── dashboard               # Configurazione Nginx

/etc/systemd/system/
└── gunicorn.service        # Service systemd

/var/log/
├── nginx/
│   ├── dashboard_access.log
│   └── dashboard_error.log
└── dashboard/
    ├── access.log          # Log Gunicorn
    └── error.log
```

---

## ⚙️ PERSONALIZZAZIONE SCRIPT

### Cambia Porta Gunicorn

Modifica nello script:
```bash
# Cerca questa riga:
--bind 127.0.0.1:8000 \\

# Cambia in:
--bind 127.0.0.1:9000 \\
```

Poi aggiorna anche Nginx:
```bash
# Nel blocco upstream:
upstream dashboard {
    server 127.0.0.1:9000 fail_timeout=0;
}
```

### Cambia Repository GitHub

Modifica all'inizio dello script:
```bash
GIT_REPO="https://github.com/TUO_USERNAME/TUO_REPO.git"
```

### Cambia Percorso Installazione

Modifica:
```bash
PROJECT_PATH="/tuo/percorso/personalizzato"
```

---

## 🎓 NOTE AVANZATE

### Modalità Non Interattiva

Se vuoi eseguire lo script senza prompt interattivi:

```bash
# Salta la creazione superuser
# Conferma automaticamente tutti i prompt
yes | sudo bash install.sh
```

### Installazione Multi-Server

Lo script può essere usato su più server:
1. Ogni server avrà il proprio database SQLite
2. Ogni server rileverà automaticamente il proprio IP
3. Per database condiviso, configura PostgreSQL manualmente

### Backup Prima dell'Installazione

```bash
# Backup directory se già esiste
sudo tar -czf /root/dashboard_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/dashboard

# Backup database
sudo cp /opt/dashboard/db.sqlite3 /root/db_backup_$(date +%Y%m%d).sqlite3
```

---

## 📞 SUPPORTO

Se hai problemi con lo script:

1. **Leggi i messaggi di errore** - Lo script mostra sempre cosa va storto
2. **Controlla i log** - Gunicorn e Nginx hanno log dettagliati
3. **Verifica prerequisiti** - Ubuntu compatibile, accesso root, internet
4. **Riesegui lo script** - È idempotente (può essere eseguito più volte)

---

## ✅ CHECKLIST POST-INSTALLAZIONE

- [ ] Dashboard accessibile da browser
- [ ] CSS caricano correttamente
- [ ] Login funziona
- [ ] Superuser creato
- [ ] Admin accessibile
- [ ] File di esempio caricati
- [ ] Gunicorn si riavvia automaticamente
- [ ] Nginx serve i file statici
- [ ] Nessun errore nei log

---

**🎉 Buon utilizzo della Dashboard!**
