# CodePulse AI

CodePulse AI is a repository intelligence platform for registering GitHub repositories, launching static-analysis scans, and reviewing repository health from a SaaS-style dashboard.

The project is split into three applications:

- `backend-core`: Spring Boot API for authentication, repository ownership, scan records, finding persistence, and internal callbacks.
- `backend-ai`: FastAPI worker for cloning repositories, parsing source files, running static-analysis tools, and sending scan results back to Spring Boot.
- `frontend`: Next.js dashboard for repository management and scan history.

## Current Capabilities

- JWT authentication with access and refresh tokens.
- User-owned GitHub repository registration.
- Repository list, detail, delete, loading, error, and empty states in the dashboard.
- Scan initiation from Spring Boot to FastAPI.
- Public GitHub repository cloning into `/tmp/codepulse/{scanId}`.
- Repository cleanup for ignored folders such as `.git`, `node_modules`, `dist`, `build`, `target`, `venv`, `.venv`, and Python cache folders.
- File metadata extraction for `.py`, `.java`, `.js`, `.ts`, `.jsx`, `.tsx`, `.json`, `.md`, `.yml`, and `.yaml`.
- Static analysis through Semgrep, Bandit, Ruff, Gitleaks, and ESLint when `package.json` exists.
- Unified finding format with severity, category, title, description, recommendation, file path, line number, and tool name.
- Internal FastAPI-to-Spring callback for `RUNNING`, `COMPLETED`, and `FAILED` scan results.
- Spring Boot persistence for scan status, findings, scores, and metadata.

## Architecture

```text
Next.js frontend
    |
    | JWT-authenticated /api requests
    v
Spring Boot backend-core
    |
    | POST /internal/analyze with INTERNAL_API_KEY
    v
FastAPI backend-ai
    |
    | clone -> clean -> parse -> static analysis
    |
    | POST /internal/scans/{scanId}/results with INTERNAL_API_KEY
    v
Spring Boot backend-core
    |
    | persist scan status, findings, metadata, scores
    v
PostgreSQL
```

Supporting services are provided by Docker Compose:

- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- Qdrant on `localhost:6333`

Redis and Qdrant are present for planned worker/RAG capabilities. The current implemented repository and scan persistence lives in PostgreSQL.

## Repository Layout

```text
.
|-- backend-core/        # Spring Boot API, auth, repositories, scans, findings
|-- backend-ai/          # FastAPI analysis worker
|-- frontend/            # Next.js dashboard
|-- docker-compose.yml   # Postgres, Redis, Qdrant
`-- README.md
```

## Prerequisites

- Java 21
- Maven or the Maven wrapper
- Python 3.11+
- Node.js 20+
- Docker Desktop
- Git

Optional scanner CLIs for full local analysis:

- `semgrep`
- `bandit`
- `ruff`
- `gitleaks`
- `npx`/ESLint for JavaScript and TypeScript repositories

If a scanner is not installed, the FastAPI analysis runner marks that tool as skipped instead of failing the entire scan.

## Environment Variables

### Spring Boot

Configured in [application.yaml](backend-core/src/main/resources/application.yaml).

| Variable | Default | Purpose |
| --- | --- | --- |
| `SERVER_PORT` | `8080` | Spring Boot port |
| `SPRING_DATASOURCE_URL` | `jdbc:postgresql://localhost:5432/codepulse` | PostgreSQL JDBC URL |
| `SPRING_DATASOURCE_USERNAME` | `codepulse` | Database user |
| `SPRING_DATASOURCE_PASSWORD` | `codepulse123` | Database password |
| `JWT_SECRET` | `your-super-secret-key-change-this-to-something-long` | JWT signing secret |
| `JWT_EXPIRATION` | `86400000` | Access token lifetime in ms |
| `JWT_REFRESH_EXPIRATION` | `604800000` | Refresh token lifetime in ms |
| `FASTAPI_BASE_URL` | `http://localhost:8000` | FastAPI internal base URL |
| `INTERNAL_API_KEY` | `change-me-internal-api-key` | Shared internal service key |
| `FRONTEND_ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origin |

### FastAPI

| Variable | Default | Purpose |
| --- | --- | --- |
| `INTERNAL_API_KEY` | `change-me-internal-api-key` | Must match Spring Boot |
| `SPRING_BOOT_BASE_URL` | `http://localhost:8080` | Spring callback base URL |
| `DATABASE_URL` | present in `backend-ai/.env` | Reserved for future AI persistence |
| `REDIS_URL` | present in `backend-ai/.env` | Reserved for future workers |
| `QDRANT_HOST` / `QDRANT_PORT` | present in `backend-ai/.env` | Reserved for vector search |
| `OPENAI_API_KEY` | present in `backend-ai/.env` | Reserved for future LLM features |

### Frontend

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8080` | Browser-facing Spring Boot API URL |

## Local Development

### 1. Start infrastructure

```powershell
docker compose up -d
```

This starts PostgreSQL, Redis, and Qdrant.

### 2. Start Spring Boot

```powershell
cd backend-core
mvn spring-boot:run
```

If your Maven wrapper works in your environment, this is equivalent:

```powershell
cd backend-core
.\mvnw.cmd spring-boot:run
```

Spring Boot runs on `http://localhost:8080`.

### 3. Start FastAPI

```powershell
cd backend-ai
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

FastAPI runs on `http://localhost:8000`.

### 4. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

The dashboard runs on `http://localhost:3000`.

## Database Migrations

Flyway migrations live in [backend-core/src/main/resources/db/migration](backend-core/src/main/resources/db/migration).

- `V3__create_repositories.sql`: user-owned repositories
- `V4__create_scans_and_findings.sql`: scans, findings, indexes, score constraints
- `V5__add_scan_metadata.sql`: scan metadata JSON storage

## API Overview

### Public Spring Boot Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Spring Boot health |
| `GET` | `/api/system/ai-health` | FastAPI health proxy |
| `POST` | `/api/auth/register` | Register user |
| `POST` | `/api/auth/login` | Login and receive tokens |
| `POST` | `/api/auth/refresh` | Refresh tokens |
| `POST` | `/api/repositories` | Add GitHub repository |
| `GET` | `/api/repositories` | List current user's repositories |
| `GET` | `/api/repositories/{id}` | Get one owned repository |
| `DELETE` | `/api/repositories/{id}` | Delete one owned repository |
| `POST` | `/api/repositories/{repositoryId}/scans` | Start scan with default branch |
| `POST` | `/api/repositories/{repositoryId}/scan` | Start scan with optional branch body |
| `GET` | `/api/repositories/{repositoryId}/scans` | List scans for repository |
| `GET` | `/api/scans/{scanId}` | Get scan detail |
| `GET` | `/api/scans/{scanId}/findings` | Page findings with optional filters |

Authenticated endpoints require:

```http
Authorization: Bearer <accessToken>
```

### Internal Endpoints

These endpoints are service-to-service only and require:

```http
Authorization: Bearer <INTERNAL_API_KEY>
```

| Service | Method | Endpoint | Description |
| --- | --- | --- | --- |
| FastAPI | `POST` | `/internal/analyze` | Accept scan work from Spring Boot |
| Spring Boot | `POST` | `/internal/scans/{scanId}/results` | Persist scan callback results |

## Example Requests

### Register and Login

```powershell
curl -X POST http://localhost:8080/api/auth/register `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"user@example.com\",\"fullName\":\"CodePulse User\",\"password\":\"password123\"}"
```

```powershell
curl -X POST http://localhost:8080/api/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"user@example.com\",\"password\":\"password123\"}"
```

### Add a Repository

```powershell
curl -X POST http://localhost:8080/api/repositories `
  -H "Authorization: Bearer <accessToken>" `
  -H "Content-Type: application/json" `
  -d "{\"repositoryUrl\":\"https://github.com/spring-projects/spring-petclinic\"}"
```

GitHub HTTPS URLs and SSH-style URLs such as `git@github.com:owner/repo.git` are accepted by Spring Boot. FastAPI cloning currently uses normalized public HTTPS GitHub URLs.

### Start a Scan

```powershell
curl -X POST http://localhost:8080/api/repositories/<repositoryId>/scan `
  -H "Authorization: Bearer <accessToken>" `
  -H "Content-Type: application/json" `
  -d "{\"branch\":\"main\"}"
```

### Fetch Findings

```powershell
curl "http://localhost:8080/api/scans/<scanId>/findings?severity=HIGH&category=security&page=0&size=20" `
  -H "Authorization: Bearer <accessToken>"
```

## Scan Lifecycle

1. A user starts a scan from Spring Boot.
2. Spring creates a `QUEUED` scan row.
3. Spring dispatches work to FastAPI with the shared internal API key.
4. FastAPI accepts the request and runs the scan in the background.
5. FastAPI sends `RUNNING` to Spring.
6. FastAPI clones the repository into `/tmp/codepulse/{scanId}`.
7. FastAPI removes ignored folders, builds a file tree, parses supported files, and runs static scanners.
8. FastAPI sends `COMPLETED` with findings, metadata, and scores, or `FAILED` with an error message.
9. Spring stores the final scan status, metadata, scores, and findings.

Supported statuses:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`

## Static Analysis

FastAPI normalizes all scanner output into this shape:

```json
{
  "severity": "HIGH",
  "category": "security",
  "title": "generic-api-key",
  "description": "A secret was detected.",
  "recommendation": "Rotate the secret.",
  "filePath": ".env",
  "lineNumber": 1,
  "toolName": "gitleaks"
}
```

Integrated scanners:

- Semgrep: static analysis
- Bandit: Python security
- Ruff: Python quality
- Gitleaks: secret detection
- ESLint: JavaScript/TypeScript quality when `package.json` exists

## Frontend Routes

| Route | Status |
| --- | --- |
| `/` | Redirects to `/repositories` through dashboard flow |
| `/repositories` | Repository dashboard |
| `/repositories/[id]` | Repository detail and scan history |
| `/dashboard` | Redirects to `/repositories` |
| `/login` | Placeholder page |
| `/register` | Placeholder page |
| `/chat`, `/reports`, `/settings` | Placeholder dashboard sections |

The implemented dashboard uses Next.js App Router, TanStack Query, Tailwind CSS, lucide-react icons, and local shadcn-style UI primitives.

## Testing

### Spring Boot

```powershell
cd backend-core
mvn test
```

Targeted scan/repository tests:

```powershell
cd backend-core
mvn test "-Dtest=RepositoryServiceTest,RepositoryControllerTest,ScanServiceTest,ScanControllerTest,InternalScanResultControllerTest"
```

### FastAPI

```powershell
cd backend-ai
.\venv\Scripts\python.exe -m unittest discover app.tests
.\venv\Scripts\python.exe -m compileall app
```

### Frontend

```powershell
cd frontend
npm run lint
npm run build
```

## Development Notes

- Root `frontend` currently has uncommitted or nested-repo state in this workspace; it was not modified while creating this README.
- The Spring Boot Maven wrapper may fail in some PowerShell environments. Use system `mvn` if that happens.
- Keep `INTERNAL_API_KEY` identical in Spring Boot and FastAPI.
- Use a strong `JWT_SECRET` outside local development.
- The scanner CLIs must be installed on the FastAPI host for full analysis coverage.
- FastAPI only clones public HTTPS GitHub repositories after Spring normalizes repository URLs.
