#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

echo "==> Validating Docker Compose files"
cd "$ROOT_DIR"
docker compose config --quiet
docker compose --profile app config --quiet
docker compose --env-file .env.example -f docker-compose.prod.yml config --quiet

echo "==> Running FastAPI tests"
cd "$ROOT_DIR/backend-ai"
if [ -x "./venv/bin/python" ]; then
  PYTHON="./venv/bin/python"
else
  PYTHON="python"
fi
$PYTHON -m unittest discover -s app/tests

echo "==> Running Spring Boot tests"
cd "$ROOT_DIR/backend-core"
mvn test

echo "==> Running frontend lint and build"
cd "$ROOT_DIR/frontend"
npm run lint
npm run build

echo "All checks completed successfully."
