#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore-postgres.sh <backup-file.sql>" >&2
  exit 2
fi

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BACKUP_FILE="$1"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
SERVICE="${POSTGRES_SERVICE:-postgres}"
DATABASE="${POSTGRES_DB:-codepulse}"
USERNAME="${POSTGRES_USER:-codepulse}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 2
fi

echo "This will restore $BACKUP_FILE into database '$DATABASE'."
echo "Make sure you have stopped application traffic and have a fresh backup."
printf "Type RESTORE to continue: "
read -r confirmation
if [ "$confirmation" != "RESTORE" ]; then
  echo "Restore cancelled." >&2
  exit 1
fi

cd "$ROOT_DIR"
docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" psql -U "$USERNAME" "$DATABASE" < "$BACKUP_FILE"
echo "Restore completed."
