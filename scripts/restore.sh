#!/bin/bash
# KitchenOS Database Restore Script
# Usage: ./restore.sh <backup_file>

set -e

BACKUP_FILE=$1
DB_NAME="kitchenos"
DB_USER="kitchenos"
DB_HOST="localhost"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -lh /var/backups/kitchenos/kitchenos_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will overwrite the current database!"
read -p "Continue? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Stopping application..."
docker-compose stop backend celery-worker celery-beat

echo "Dropping and recreating database..."
dropdb -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" --if-exists
createdb -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}"

echo "Restoring from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}"

echo "Starting application..."
docker-compose start backend celery-worker celery-beat

echo "Restore completed successfully!"
