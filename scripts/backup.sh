#!/bin/bash
# Script di backup per database PostgreSQL

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="talent_mosaic"
DB_USER="talent_user"
DB_HOST="192.168.1.11"

# Crea directory backup
mkdir -p $BACKUP_DIR

echo "🔄 Inizio backup $DATE..."

# Backup database PostgreSQL
echo "📦 Backup database..."
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
echo "📁 Backup media files..."
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /opt/talent/app media/

# Mantieni solo ultimi 30 giorni
echo "🧹 Pulizia backup vecchi..."
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "✅ Backup completato: $BACKUP_DIR"
ls -lh $BACKUP_DIR/*_$DATE.*
