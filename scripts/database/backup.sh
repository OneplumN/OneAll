#!/usr/bin/env bash
set -euo pipefail

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=${BACKUP_DIR:-"backups/$DATE"}
mkdir -p "$BACKUP_DIR"

echo "[OneAll] Dumping MySQL schema..."
mysqldump -h ${MYSQL_HOST:-127.0.0.1} -P ${MYSQL_PORT:-3306} \
  -u ${MYSQL_USER:-root} -p${MYSQL_PASSWORD:-root} \
  --databases ${MYSQL_DB:-oneall} > "$BACKUP_DIR/mysql.sql"

echo "[OneAll] Dumping TimescaleDB..."
pg_dump -h ${PG_HOST:-127.0.0.1} -p ${PG_PORT:-5432} \
  -U ${PG_USER:-postgres} ${PG_DB:-oneall_metrics} > "$BACKUP_DIR/timescale.sql"

echo "[OneAll] Backups stored in $BACKUP_DIR"
