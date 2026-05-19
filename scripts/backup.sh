#!/bin/bash
# KitchenOS Database Backup Script
# Run via cron: 0 2 * * * /path/to/backup.sh

set -e

# Configuration
BACKUP_DIR="/var/backups/kitchenos"
RETENTION_DAYS=30
DB_NAME="kitchenos"
DB_USER="kitchenos"
DB_HOST="localhost"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/kitchenos_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create backup
echo "Starting backup at $(date)"
pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# Verify backup
if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "Backup completed: ${BACKUP_FILE} (${SIZE})"
else
    echo "ERROR: Backup failed!"
    exit 1
fi

# Upload to S3 (if configured)
if [ -n "${AWS_S3_BUCKET}" ]; then
    aws s3 cp "${BACKUP_FILE}" "s3://${AWS_S3_BUCKET}/backups/"
    echo "Uploaded to S3"
fi

# Clean old backups
echo "Cleaning backups older than ${RETENTION_DAYS} days"
find "${BACKUP_DIR}" -name "kitchenos_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup process completed at $(date)"
