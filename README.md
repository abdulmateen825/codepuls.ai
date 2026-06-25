# CodePulse AI

CodePulse AI is an open-source repository intelligence platform for registering GitHub repositories, launching static-analysis scans, detecting code smells, reviewing repository health, chatting with repository context, and generating PDF reports.

The application is intentionally split into three services:

```text
Browser -> Next.js frontend -> Spring Boot core backend -> FastAPI AI service
```

The frontend must call Spring Boot only. FastAPI is an internal service and should never be exposed directly to browsers.

## Main Features

- JWT authentication with access and refresh tokens.
- User-owned GitHub repository registration.
- Repository dashboard with list, detail, delete, empty, loading, and error states.
- Scan initiation from Spring Boot to FastAPI.
- Public GitHub repository cloning into a temporary workspace.
- Source-file discovery and metadata extraction for Python, Java, JavaScript, TypeScript, JSON, Markdown, YAML, and related extensions.
- Static analysis through Semgrep, Bandit, Ruff, Gitleaks, and ESLint when available.
- Deterministic code-smell detection.
- Stored bounded source snippets and line context for findings.
- Health score calculation.
- Repository chat through Spring Boot and FastAPI internal calls.
- AI finding explanations.
- PDF report generation and download.
- PostgreSQL persistence for users, repositories, scans, findings, reports, and metadata.
- Qdrant integration for repository code chunks and semantic retrieval.

## Code-Smell Functionality

Code-smell detection runs in FastAPI after repository parsing and before the scan callback to Spring Boot. Detection is deterministic and does not use an LLM as the primary detector.

Current smell types:

- `LONG_METHOD`
- `LARGE_CLASS`
- `HIGH_CYCLOMATIC_COMPLEXITY`
- `DEEP_NESTING`
- `LONG_PARAMETER_LIST`
- `DUPLICATED_CODE`
- `DEAD_CODE`
- `GOD_OBJECT`

Code-smell findings use:

```json
{
  "category": "CODE_SMELL",
  "ruleId": "LONG_METHOD",
  "smellType": "LONG_METHOD",
  "severity": "MEDIUM",
  "language": "PYTHON",
  "filePath": "src/app.py",
  "startLine": 10,
  "endLine": 80
}
```

Spring Boot stores code-smell fields as nullable columns so older scanner findings remain compatible. The frontend supports filtering by category, smell type, severity, language, and file path.

## Technology Stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, TanStack Query, Recharts |
| Core backend | Spring Boot, Spring Security, JPA, Flyway, PostgreSQL |
| AI/analysis backend | FastAPI, Python, deterministic parsers/scanners |
| Static analysis | Semgrep, Bandit, Ruff, Gitleaks, ESLint |
| Vector search | Qdrant |
| Infrastructure | Docker Compose, service Dockerfiles, Nginx reverse proxy |

## Service Responsibilities

### `frontend`

- Browser UI.
- Calls Spring Boot `/api` endpoints.
- Does not call FastAPI directly.
- Renders repository, scan, finding, chat, and report experiences.

### `backend-core`

- Authentication and JWT issuance.
- Repository ownership and access control.
- Scan records and finding persistence.
- Internal callback receiver from FastAPI.
- Report metadata and download endpoint.
- Public API used by the frontend.

### `backend-ai`

- Internal FastAPI service.
- Clones public GitHub repositories.
- Discovers and parses files.
- Runs static-analysis tools.
- Runs code-smell detectors.
- Calculates health score inputs.
- Generates PDF bytes.
- Calls Spring Boot internal callback endpoints.

## Folder Structure

```text
.
|-- backend-ai/                 # FastAPI analysis service
|   `-- app/
|-- backend-core/               # Spring Boot API
|   `-- src/
|-- docs/                       # Deployment and operations docs
|-- frontend/                   # Next.js dashboard
|   `-- src/
|-- .github/                    # Issue and PR templates
|-- nginx/                      # Reverse proxy template
|-- scripts/                    # Test, smoke, backup, and restore scripts
|-- docker-compose.yml          # Local infrastructure services
|-- docker-compose.prod.yml     # Production-ready Compose template
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- CODE_OF_CONDUCT.md
|-- LICENSE
`-- README.md
```

## Prerequisites

- Java 21
- Maven or the Maven wrapper
- Python 3.11+
- Node.js 20+
- Docker Desktop or Docker Engine
- Git

Optional scanner CLIs for full local analysis:

- `semgrep`
- `bandit`
- `ruff`
- `gitleaks`
- `npx` and ESLint for JavaScript/TypeScript repositories

If a scanner is missing, FastAPI marks that tool as skipped instead of failing the full scan.

## Local Installation

### 1. Clone the repository

```powershell
git clone <repository-url>
cd codepuls.ai
```

### 2. Start infrastructure

```powershell
docker compose up -d
```

By default, local Compose starts PostgreSQL, Redis, and Qdrant. To build and run all app services locally through Docker, use the `app` profile:

```powershell
docker compose --profile app up -d --build
```

### 3. Start Spring Boot

```powershell
cd backend-core
mvn spring-boot:run
```

If your Maven wrapper works locally:

```powershell
cd backend-core
.\mvnw.cmd spring-boot:run
```

Spring Boot runs on `http://localhost:8080`.

### 4. Start FastAPI

```powershell
cd backend-ai
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

FastAPI runs on `http://localhost:8000`.

### 5. Start Next.js

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000`.

## Manual Local Setup

If you do not use Docker for infrastructure, provide:

- PostgreSQL database named `codepulse`.
- Redis reachable by `REDIS_URL`.
- Qdrant reachable by `QDRANT_URL` or `QDRANT_HOST` and `QDRANT_PORT`.

Then configure Spring Boot and FastAPI environment variables as described below.

## Docker Local Setup

Infrastructure-only:

```powershell
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

Full local app stack:

```powershell
docker compose --profile app up -d --build
docker compose --profile app ps
docker compose --profile app logs -f
docker compose --profile app down
```

Production template validation:

```powershell
docker compose --env-file .env.example -f docker-compose.prod.yml config --quiet
```

## Environment Variables

Do not commit real secrets. Copy `.env.example` to `.env` for Docker Compose or use the variable names below in your local shell.

### Frontend

| Variable | Purpose | Safe local example |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-facing Spring Boot URL | `http://localhost:8080` |
| `CORE_API_BASE_URL` | Server-rendered health page Spring Boot URL | `http://localhost:8080` |

Only `NEXT_PUBLIC_*` variables are exposed to the browser. Never put internal API keys or database credentials in frontend env vars.

### Spring Boot

| Variable | Purpose | Safe local example |
| --- | --- | --- |
| `SERVER_PORT` | HTTP port | `8080` |
| `SPRING_DATASOURCE_URL` | PostgreSQL JDBC URL | `jdbc:postgresql://localhost:5432/codepulse` |
| `SPRING_DATASOURCE_USERNAME` | Database user | `codepulse` |
| `SPRING_DATASOURCE_PASSWORD` | Database password | `change-me-local` |
| `JWT_SECRET` | JWT signing secret | long random local value |
| `JWT_EXPIRATION` | Access token lifetime in ms | `86400000` |
| `JWT_REFRESH_EXPIRATION` | Refresh token lifetime in ms | `604800000` |
| `FASTAPI_BASE_URL` | Internal FastAPI URL | `http://localhost:8000` |
| `INTERNAL_API_KEY` | Shared internal service key | long random local value |
| `FRONTEND_ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |
| `GITHUB_CLIENT_ID` | Optional OAuth client id | empty for local |
| `GITHUB_CLIENT_SECRET` | Optional OAuth client secret | empty for local |

Optional open-source mode variables:

| Variable | Purpose | Safe local example |
| --- | --- | --- |
| `OPEN_SOURCE_MODE` | Marks the app as community/self-hosted | `true` |
| `ENFORCE_USAGE_LIMITS` | Enables optional usage caps | `false` |
| `MAX_SCANS_PER_USER` | Maximum stored scans per owner when limits are enabled | `0` |
| `MAX_REPOSITORY_SIZE_MB` | Optional FastAPI repository size cap, `0` disables | `0` |
| `MAX_CONCURRENT_SCANS` | Reserved operational cap | `0` |

### FastAPI

| Variable | Purpose | Safe local example |
| --- | --- | --- |
| `INTERNAL_API_KEY` | Must match Spring Boot | long random local value |
| `SPRING_BOOT_BASE_URL` | Spring callback URL | `http://localhost:8080` |
| `QDRANT_URL` | Qdrant URL | `http://localhost:6333` |
| `QDRANT_HOST` | Qdrant host fallback | `localhost` |
| `QDRANT_PORT` | Qdrant port fallback | `6333` |
| `QDRANT_COLLECTION` | Vector collection | `codepulse_chunks` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379` |
| `LLM_PROVIDER` | `fallback` or `openai` | `fallback` |
| `OPENAI_API_KEY` | Optional OpenAI key | empty unless used |
| `EMBEDDING_PROVIDER` | `local` or `openai` | `local` |
| `EMBEDDING_MODEL` | Local embedding model | `sentence-transformers/all-MiniLM-L6-v2` |

Code-smell threshold variables:

- `CODE_SMELL_MAX_METHOD_LINES`
- `CODE_SMELL_MAX_CLASS_LINES`
- `CODE_SMELL_MAX_COMPLEXITY`
- `CODE_SMELL_MAX_NESTING_DEPTH`
- `CODE_SMELL_MAX_PARAMETER_COUNT`
- `CODE_SMELL_MIN_DUPLICATE_LINES`
- `CODE_SMELL_GOD_OBJECT_MIN_METHODS`
- `CODE_SMELL_GOD_OBJECT_MIN_FIELDS`
- `CODE_SMELL_MAX_SNIPPET_LINES`
- `CODE_SMELL_CONTEXT_LINES`
- `CODE_SMELL_MAX_FILE_BYTES`
- `CODE_SMELL_MAX_SOURCE_CHARS`

FastAPI deployment variables:

| Variable | Purpose | Safe local example |
| --- | --- | --- |
| `REPOSITORY_CLONE_TIMEOUT_SECONDS` | Git clone timeout | `180` |
| `MAX_REPOSITORY_SIZE_MB` | Optional repository size cap | `0` |
| `MAX_FILE_COUNT` | Maximum parsed files | `5000` |
| `MAX_INDIVIDUAL_FILE_SIZE_BYTES` | Maximum parsed file size | `1000000` |
| `MAX_SCAN_TIME_SECONDS` | Reserved scan runtime cap | `0` |
| `CODEPULSE_WORKSPACE_ROOT` | Temporary clone workspace | `/tmp/codepulse` |
| `REPORT_PATH` | Generated report workspace | `/tmp/codepulse-reports` |
| `SCANNER_TIMEOUT_SECONDS` | Per-tool scanner timeout | `120` |
| `GIT_PATH` | Git executable path | `git` |
| `SEMGREP_PATH` | Semgrep executable path | `semgrep` |
| `BANDIT_PATH` | Bandit executable path | `bandit` |
| `RUFF_PATH` | Ruff executable path | `ruff` |
| `GITLEAKS_PATH` | Gitleaks executable path | `gitleaks` |
| `NPX_PATH` | NPX executable path | `npx` |

## Database Migrations

Flyway migrations live in `backend-core/src/main/resources/db/migration`.

| Migration | Purpose |
| --- | --- |
| `V3__create_repositories.sql` | User-owned repositories |
| `V4__create_scans_and_findings.sql` | Scans, findings, indexes, score constraints |
| `V5__add_scan_metadata.sql` | Scan metadata JSON |
| `V6__create_reports.sql` | PDF report storage |
| `V7__add_code_smell_finding_fields.sql` | Code-smell metadata and source context |

Spring Boot runs Flyway during startup.

## API Flow

### Scan initiation

```text
Frontend
  -> POST /api/repositories/{repositoryId}/scan
Spring Boot
  -> creates QUEUED scan
  -> POST FastAPI /internal/analyze with INTERNAL_API_KEY
FastAPI
  -> clones, parses, scans, detects code smells
  -> POST Spring /internal/scans/{scanId}/results
Spring Boot
  -> stores status, metadata, scores, findings
Frontend
  -> GET /api/scans/{scanId}
  -> GET /api/scans/{scanId}/findings
```

### Important public Spring Boot endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Core health |
| `GET` | `/api/system/ai-health` | FastAPI health through Spring |
| `POST` | `/api/auth/register` | Register |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/auth/refresh` | Refresh tokens |
| `POST` | `/api/repositories` | Add repository |
| `GET` | `/api/repositories` | List repositories |
| `GET` | `/api/repositories/{id}` | Repository detail |
| `DELETE` | `/api/repositories/{id}` | Delete repository |
| `POST` | `/api/repositories/{repositoryId}/scan` | Start scan |
| `GET` | `/api/repositories/{repositoryId}/scans` | Scan history |
| `GET` | `/api/scans/{scanId}` | Scan detail |
| `GET` | `/api/scans/{scanId}/findings` | Findings with filters |
| `GET` | `/api/findings/{findingId}/source` | Stored bounded source context |
| `POST` | `/api/findings/{findingId}/explain` | Explain finding |
| `POST` | `/api/repositories/{repositoryId}/chat` | Repository chat |
| `POST` | `/api/scans/{scanId}/reports` | Create report |
| `GET` | `/api/reports` | List reports |
| `GET` | `/api/reports/{reportId}/download` | Download report |

### Internal endpoints

Internal endpoints require:

```http
Authorization: Bearer <INTERNAL_API_KEY>
```

| Service | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| FastAPI | `POST` | `/internal/analyze` | Accept scan work |
| FastAPI | `POST` | `/internal/repositories/chat` | Answer repository chat |
| FastAPI | `POST` | `/internal/findings/explain` | Explain a finding |
| FastAPI | `POST` | `/internal/reports/pdf` | Generate report bytes |
| Spring Boot | `POST` | `/internal/scans/{scanId}/results` | Receive scan callback |

## Security Model

- The frontend calls Spring Boot only.
- FastAPI is internal and protected by `INTERNAL_API_KEY`.
- Spring Boot enforces authenticated ownership for user repositories, scans, findings, chat, and reports.
- Static-analysis tools are launched with argument arrays, not shell strings.
- Cloned repository code is parsed and scanned but never executed.
- Finding source responses return stored bounded snippets, not full repository files.
- Production deployments should expose only Nginx publicly.
- PostgreSQL, Redis, Qdrant, and FastAPI should stay on private Docker networks.
- JWT secrets, database passwords, internal API keys, Redis credentials, Qdrant credentials, and LLM keys must never be exposed to the browser.

## Testing Commands

Run the full local verification suite:

```powershell
.\scripts\test-all.ps1
```

On POSIX shells:

```bash
scripts/test-all.sh
```

### Spring Boot

```powershell
cd backend-core
mvn test
```

Targeted tests:

```powershell
cd backend-core
mvn test "-Dtest=RepositoryServiceTest,RepositoryControllerTest,ScanServiceTest,ScanControllerTest,InternalScanResultControllerTest,AiInteractionServiceTest,ReportServiceTest"
```

### FastAPI

```powershell
cd backend-ai
.\venv\Scripts\python.exe -m unittest discover -s app\tests
```

### Frontend

```powershell
cd frontend
npm run lint
npm run build
```

## Common Errors

### Maven wrapper fails in PowerShell

Use system Maven:

```powershell
cd backend-core
mvn test
```

### Spring Boot cannot connect to PostgreSQL

Start local infrastructure:

```powershell
docker compose up -d postgres
```

Confirm `SPRING_DATASOURCE_URL`, username, and password match your local database.

### FastAPI says a scanner is missing

Install the optional scanner CLI or treat the skipped scanner as expected for local development.

### Frontend cannot reach the API

Set:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8080"
```

Then restart `npm run dev`.

### FastAPI callback is unauthorized

Ensure `INTERNAL_API_KEY` has the same value in Spring Boot and FastAPI.

## Backup And Restore

Use the scripts in `scripts/` for repeatable backups and restores. See `docs/OPERATIONS.md` for the runbook.

### PostgreSQL backup

```powershell
.\scripts\backup-postgres.ps1
```

### PostgreSQL restore

Restoring overwrites data. Verify the target database before running restore commands.

```powershell
.\scripts\restore-postgres.ps1 -BackupFile .\backups\codepulse-postgres-YYYYMMDD-HHMMSS.sql
```

### Qdrant

Qdrant stores embeddings for code chunks. If Qdrant data is lost, embeddings can usually be regenerated by rescanning repositories. Production deployments should use Qdrant snapshots or volume backups.

### Reports

Reports are stored in PostgreSQL as bytes. PostgreSQL backups include reports.

### Redis

Redis is currently not the source of durable application data. If later worker queues depend on Redis durability, enable persistence and back up the Redis volume.

Recommended backup posture:

- daily PostgreSQL backups,
- weekly full volume backups,
- encrypted off-server copies,
- regular restore testing.

## Production Deployment

Do not deploy from this repository without reviewing production values.

Simple VPS flow:

1. Provision an Ubuntu server.
2. Install Docker Engine and Docker Compose.
3. Create a non-root deployment user.
4. Configure firewall rules so only HTTP/HTTPS/SSH are public.
5. Point a domain to the server.
6. Clone this repository.
7. Copy `.env.example` to `.env`.
8. Fill production values with strong secrets.
9. Start with production Compose:

   ```bash
   docker compose --env-file .env -f docker-compose.prod.yml up -d --build
   ```

10. Verify health.
11. Configure HTTPS using the Nginx TLS template.
12. Configure backups and monitoring.

See `docs/DEPLOYMENT.md` for the full guide.

## Upgrade Process

Recommended future upgrade flow:

1. Read release notes.
2. Back up PostgreSQL and persistent volumes.
3. Pull the new version.
4. Review environment variable changes.
5. Validate Compose config.
6. Build images.
7. Start services.
8. Verify health endpoints.
9. Run smoke tests.

## Rollback Process

Recommended future rollback flow:

1. Stop new containers.
2. Start the previous known-good image or checkout.
3. Restore database only if a migration or data change requires it.
4. Verify `/api/health`, frontend access, scan initiation, and report download.
5. Review logs for failed callbacks or incomplete scans.

## Contribution Instructions

See `CONTRIBUTING.md` for contribution guidelines.

Before opening a pull request:

- run relevant tests,
- update documentation,
- keep the frontend calling Spring Boot only,
- avoid committing secrets,
- preserve existing architecture and ownership checks.

## License

CodePulse AI is licensed under the Apache License 2.0. See `LICENSE`.
