#!/bin/bash
set -e

# Configuration
NAMESPACE="meter-reading"
BACKUP_DIR="/backups/meter-reading"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
POSTGRES_POD=$(kubectl get pods -n ${NAMESPACE} -l app=postgres -o jsonpath='{.items[0].metadata.name}')

echo "🔄 Starting backup process..."

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup PostgreSQL
echo "📦 Backing up PostgreSQL database..."
kubectl exec -n ${NAMESPACE} ${POSTGRES_POD} -- pg_dump -U postgres meter_readings | gzip > ${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz

# Backup Kubernetes resources
echo "📦 Backing up Kubernetes resources..."
kubectl get all -n ${NAMESPACE} -o yaml > ${BACKUP_DIR}/k8s_resources_${TIMESTAMP}.yaml

# Backup secrets and configmaps
kubectl get secrets -n ${NAMESPACE} -o yaml > ${BACKUP_DIR}/secrets_${TIMESTAMP}.yaml
kubectl get configmaps -n ${NAMESPACE} -o yaml > ${BACKUP_DIR}/configmaps_${TIMESTAMP}.yaml

echo "✅ Backup completed: ${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"

# Cleanup old backups (keep last 7 days)
find ${BACKUP_DIR} -name "*.gz" -mtime +7 -delete
echo "🗑️  Cleaned up old backups"