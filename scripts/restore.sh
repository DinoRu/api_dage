#!/bin/bash
set -e

# Configuration
NAMESPACE="meter-reading"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh <backup_file.sql.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

POSTGRES_POD=$(kubectl get pods -n ${NAMESPACE} -l app=postgres -o jsonpath='{.items[0].metadata.name}')

echo "⚠️  WARNING: This will restore the database from backup."
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "🔄 Starting restore process..."

# Scale down API pods
echo "⏸️  Scaling down API..."
kubectl scale deployment/api-deployment -n ${NAMESPACE} --replicas=0

# Restore database
echo "📥 Restoring database..."
gunzip -c ${BACKUP_FILE} | kubectl exec -i -n ${NAMESPACE} ${POSTGRES_POD} -- psql -U postgres meter_readings

# Scale up API pods
echo "▶️  Scaling up API..."
kubectl scale deployment/api-deployment -n ${NAMESPACE} --replicas=3

echo "✅ Restore completed successfully!"