from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    environment: str = "local"
    service_port: int = 8000
    internal_api_key: str = "change-me-internal-api-key"
    spring_boot_base_url: str = "http://localhost:8080"
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    llm_provider: str = "fallback"
    openai_api_key: str | None = None
    embedding_provider: str = "local"
    clone_timeout_seconds: int = 180
    scanner_timeout_seconds: int = 120
    max_repository_size_mb: int = 0
    max_file_count: int = 5000
    max_individual_file_size_bytes: int = 1_000_000
    max_scan_time_seconds: int = 0
    workspace_root: Path = Path("/tmp/codepulse")
    report_path: Path = Path("/tmp/codepulse-reports")
    log_level: str = "INFO"
    git_path: str = "git"
    semgrep_path: str = "semgrep"
    bandit_path: str = "bandit"
    ruff_path: str = "ruff"
    gitleaks_path: str = "gitleaks"
    npx_path: str = "npx"

    @property
    def require_strong_secrets(self) -> bool:
        return _bool_env("REQUIRE_STRONG_SECRETS", self.environment.lower() in {"prod", "production"})


def load_settings() -> Settings:
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = os.getenv("QDRANT_PORT", "6333")
    return Settings(
        environment=os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local")).strip().lower(),
        service_port=_int_env("FASTAPI_PORT", 8000),
        internal_api_key=os.getenv("INTERNAL_API_KEY", "change-me-internal-api-key"),
        spring_boot_base_url=os.getenv("SPRING_BOOT_BASE_URL", "http://localhost:8080").rstrip("/"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        qdrant_url=os.getenv("QDRANT_URL", f"http://{qdrant_host}:{qdrant_port}").rstrip("/"),
        qdrant_api_key=_optional_env("QDRANT_API_KEY"),
        llm_provider=os.getenv("LLM_PROVIDER", "fallback").strip().lower(),
        openai_api_key=_optional_env("OPENAI_API_KEY"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "local").strip().lower(),
        clone_timeout_seconds=_int_env("REPOSITORY_CLONE_TIMEOUT_SECONDS", 180),
        scanner_timeout_seconds=_int_env("SCANNER_TIMEOUT_SECONDS", 120),
        max_repository_size_mb=_int_env("MAX_REPOSITORY_SIZE_MB", 0),
        max_file_count=_int_env("MAX_FILE_COUNT", 5000),
        max_individual_file_size_bytes=_int_env("MAX_INDIVIDUAL_FILE_SIZE_BYTES", 1_000_000),
        max_scan_time_seconds=_int_env("MAX_SCAN_TIME_SECONDS", 0),
        workspace_root=Path(os.getenv("CODEPULSE_WORKSPACE_ROOT", "/tmp/codepulse")),
        report_path=Path(os.getenv("REPORT_PATH", "/tmp/codepulse-reports")),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        git_path=os.getenv("GIT_PATH", "git"),
        semgrep_path=os.getenv("SEMGREP_PATH", "semgrep"),
        bandit_path=os.getenv("BANDIT_PATH", "bandit"),
        ruff_path=os.getenv("RUFF_PATH", "ruff"),
        gitleaks_path=os.getenv("GITLEAKS_PATH", "gitleaks"),
        npx_path=os.getenv("NPX_PATH", "npx"),
    )


def validate_startup_settings(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    errors = []

    if settings.require_strong_secrets:
        if not settings.internal_api_key or settings.internal_api_key == "change-me-internal-api-key":
            errors.append("INTERNAL_API_KEY must be set to a strong non-default value.")
        if settings.llm_provider == "openai" and not settings.openai_api_key:
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        if settings.embedding_provider == "openai" and not settings.openai_api_key:
            errors.append("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")

    settings.workspace_root.mkdir(parents=True, exist_ok=True)
    settings.report_path.mkdir(parents=True, exist_ok=True)

    if errors:
        raise RuntimeError("Invalid FastAPI configuration: " + " ".join(errors))

    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
    logger.info("FastAPI configuration validated for environment=%s", settings.environment)


def scanner_path(tool_name: str) -> str:
    settings = get_settings()
    return {
        "git": settings.git_path,
        "semgrep": settings.semgrep_path,
        "bandit": settings.bandit_path,
        "ruff": settings.ruff_path,
        "gitleaks": settings.gitleaks_path,
        "npx": settings.npx_path,
    }.get(tool_name, tool_name)


def get_settings() -> Settings:
    return load_settings()


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
