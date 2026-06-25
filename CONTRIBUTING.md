# Contributing to CodePulse AI

Thank you for helping improve CodePulse AI. This project is intended to stay open-source friendly, easy to run locally, and safe to deploy later through configuration.

## Ground Rules

- Preserve the architecture: Browser -> Next.js -> Spring Boot -> FastAPI.
- The frontend must call Spring Boot only. Do not call FastAPI directly from browser code.
- Do not commit secrets, tokens, private repository URLs, production domains, or real credentials.
- Keep changes focused. Avoid unrelated rewrites or broad refactors.
- Add or update tests when changing behavior.
- Keep payment and subscription dependencies out of the core application.

## Local Development

1. Copy `.env.example` to `.env` when it exists.
2. Start infrastructure with Docker Compose.
3. Run Spring Boot, FastAPI, and Next.js locally.
4. Run the relevant tests before opening a pull request.

Useful commands are documented in `README.md`.

## Pull Request Checklist

- [ ] The change is scoped to one clear purpose.
- [ ] Tests were added or updated where useful.
- [ ] Existing tests pass locally.
- [ ] Documentation was updated for user-facing or operational changes.
- [ ] No secrets or private URLs were committed.
- [ ] Docker and environment changes remain configurable.

## Coding Guidelines

### Spring Boot

- Use DTOs for API requests and responses.
- Enforce authenticated ownership in service methods.
- Keep controllers thin and business rules in services.
- Use Flyway migrations for schema changes.

### FastAPI

- Keep scanning deterministic unless a feature explicitly requires an LLM.
- Never execute repository code.
- Use argument arrays for external commands.
- Bound timeouts and payload sizes.
- Handle partial scanner failures without failing the whole scan when possible.

### Frontend

- Use Spring Boot APIs only.
- Escape source code and markdown-like content safely.
- Keep loading, empty, and error states clear.
- Preserve the dashboard-oriented SaaS UI style.

## Reporting Issues

Use the GitHub issue templates for bugs and feature requests. For security issues, follow `SECURITY.md` instead of opening a public issue.
