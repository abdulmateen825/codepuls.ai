#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-backups}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
SERVICE="${POSTGRES_SERVICE:-postgres}"
DATABASE="${POSTGRES_DB:-codepulse}"
USERNAME="${POSTGRES_USER:-codepulse}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$ROOT_DIR/$OUTPUT_DIR"
OUTPUT_FILE="$ROOT_DIR/$OUTPUT_DIR/codepulse-postgres-$TIMESTAMP.sql"

echo "==> Creating PostgreSQL backup at $OUTPUT_FILE"
cd "$ROOT_DIR"
docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" pg_dump -U "$USERNAME" "$DATABASE" > "$OUTPUT_FILE"
echo "Backup completed: $OUTPUT_FILE"
