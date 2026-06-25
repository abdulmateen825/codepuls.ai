# Production Deployment Guide

This guide prepares CodePulse AI for a simple VPS deployment, such as DigitalOcean, without deploying automatically.

## Architecture

Production traffic should follow this path:

```text
Internet -> Nginx -> Next.js frontend -> Spring Boot backend-core -> FastAPI backend-ai
```

Only Nginx should be exposed publicly. Spring Boot, FastAPI, PostgreSQL, Redis, and Qdrant stay on the private Docker network.

## Prerequisites

- Ubuntu server or equivalent Linux host
- Docker Engine and Docker Compose plugin
- A non-root deploy user
- Firewall allowing only SSH, HTTP, and HTTPS
- Domain DNS pointing to the server

## Prepare Environment

Copy the example file and replace every placeholder secret:

```bash
cp .env.example .env
```

Required production values:

- `APP_ENV=production`
- `POSTGRES_PASSWORD`
- `JWT_SECRET`
- `INTERNAL_API_KEY`
- `FRONTEND_ALLOWED_ORIGINS`
- `LLM_PROVIDER` and `OPENAI_API_KEY`, only when OpenAI-backed features are enabled
- `QDRANT_API_KEY`, if using a secured external Qdrant instance

Never put private service keys in `NEXT_PUBLIC_*` variables. Those values are browser-visible.

## Validate Configuration

```bash
docker compose --env-file .env -f docker-compose.prod.yml config --quiet
```

## Build And Start

```bash
docker compose --env-file .env -f docker-compose.prod.yml up -d --build
```

## Health Checks

```bash
curl --fail http://localhost/nginx-health
curl --fail http://localhost/api/health
```

Run the smoke script from the server:

```bash
scripts/smoke-test.sh nginx
```

## TLS

The Nginx config includes a commented TLS-ready server block. Add certificates with your preferred ACME client, mount them into the Nginx container, enable port `443`, and redirect HTTP to HTTPS after verification.

## Updates

1. Back up PostgreSQL.
2. Pull or copy the new release.
3. Review `.env.example` for new variables.
4. Validate Compose config.
5. Rebuild and restart.
6. Run smoke tests.

```bash
scripts/backup-postgres.sh
docker compose --env-file .env -f docker-compose.prod.yml config --quiet
docker compose --env-file .env -f docker-compose.prod.yml up -d --build
scripts/smoke-test.sh nginx
```

## Rollback

1. Stop the current containers.
2. Check out the previous known-good version.
3. Start services with the previous Compose definition.
4. Restore PostgreSQL only when a database migration or data change requires it.
5. Run smoke tests.

## Security Notes

- Keep FastAPI internal.
- Keep `/internal/*` unreachable from Nginx.
- Rotate `JWT_SECRET` and `INTERNAL_API_KEY` if exposed.
- Prefer HTTPS-only cookies and strict CORS in production.
- Tighten Content Security Policy after validating Next.js runtime requirements.
