#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
CORE_URL="${CORE_URL:-http://localhost:8080}"
MODE="${1:-local}"

check_url() {
  name="$1"
  url="$2"
  echo "==> $name $url"
  curl --fail --silent --show-error --max-time 15 "$url" >/dev/null
}

if [ "$MODE" = "nginx" ]; then
  check_url "Nginx health" "$BASE_URL/nginx-health"
  check_url "Spring health through Nginx" "$BASE_URL/api/health"
  check_url "Frontend through Nginx" "$BASE_URL/"
else
  check_url "Frontend health" "$FRONTEND_URL/api/health"
  check_url "Spring health" "$CORE_URL/api/health"
fi

echo "Smoke test completed successfully."
