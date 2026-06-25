# Security Policy

## Supported Versions

This repository is early-stage open-source software. Security fixes should target the main branch unless a maintained release branch is documented later.

## Reporting A Vulnerability

Please do not open a public issue for a suspected vulnerability.

Until a private security contact is published, create a private advisory in the repository if GitHub Security Advisories are enabled. If private advisories are not available, contact the maintainers through the repository owner profile and include only enough detail to establish contact safely.

Do not include:

- real API keys,
- JWTs,
- passwords,
- private repository contents,
- production database dumps,
- full source files from private repositories.

## Security Model

- Browser traffic should reach only the Next.js frontend and Spring Boot `/api` routes.
- FastAPI internal routes must remain private and protected by `INTERNAL_API_KEY`.
- PostgreSQL, Redis, and Qdrant should not be publicly exposed in production.
- JWT secrets, database passwords, internal API keys, and LLM keys must come from environment variables.
- Static analysis and code-smell detection must never execute cloned repository code.

## Local Secrets

Use `.env` files for local development only. Do not commit real secrets. The committed `.env.example` file should contain placeholders only.

## Dependency And Container Scanning

Pull requests should run dependency and container/security scans when workflows are enabled. Scanner findings should be triaged before releases.
