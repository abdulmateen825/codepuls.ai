import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings, scanner_path


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    title: str
    description: str
    recommendation: str
    filePath: str
    lineNumber: int
    toolName: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ScannerResult:
    toolName: str
    status: str
    findings: list[dict]
    error: str | None = None

    def to_dict(self) -> dict:
        result = {
            "toolName": self.toolName,
            "status": self.status,
            "findingCount": len(self.findings),
        }
        if self.error:
            result["error"] = self.error
        return result


class BaseScanner(ABC):
    tool_name: str
    category: str

    @abstractmethod
    def scan(self, repository_path: Path) -> ScannerResult:
        raise NotImplementedError

    def _run_json_command(
        self,
        command: list[str],
        repository_path: Path,
        allowed_finding_exit_codes: set[int] | None = None,
    ) -> tuple[Any | None, str | None]:
        allowed_finding_exit_codes = allowed_finding_exit_codes or set()
        command = [scanner_path(command[0]), *command[1:]]
        timeout_seconds = get_settings().scanner_timeout_seconds

        try:
            completed = subprocess.run(
                command,
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return None, f"{command[0]} is not installed or is not available on PATH."
        except subprocess.TimeoutExpired:
            return None, f"{command[0]} timed out after {timeout_seconds} seconds."

        output = completed.stdout.strip()
        if not output:
            if completed.returncode == 0 or completed.returncode in allowed_finding_exit_codes:
                return [] if command[0] in {"ruff", "gitleaks"} else {}, None
            return None, completed.stderr.strip() or f"{command[0]} exited with code {completed.returncode}."

        try:
            return json.loads(output), None
        except json.JSONDecodeError:
            if completed.returncode == 0 or completed.returncode in allowed_finding_exit_codes:
                return None, f"{command[0]} returned invalid JSON output."
            return None, completed.stderr.strip() or f"{command[0]} exited with code {completed.returncode}."

    def _completed(self, findings: list[Finding]) -> ScannerResult:
        return ScannerResult(
            toolName=self.tool_name,
            status="completed",
            findings=[finding.to_dict() for finding in findings],
        )

    def _skipped(self, error: str) -> ScannerResult:
        return ScannerResult(
            toolName=self.tool_name,
            status="skipped",
            findings=[],
            error=error,
        )

    def _failed(self, error: str) -> ScannerResult:
        return ScannerResult(
            toolName=self.tool_name,
            status="failed",
            findings=[],
            error=error,
        )

    def _relative_path(self, path: str | None, repository_path: Path) -> str:
        if not path:
            return ""

        root = repository_path.resolve()
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = root / candidate

        try:
            return candidate.resolve().relative_to(root).as_posix()
        except ValueError:
            return str(path).replace("\\", "/")

    def _line_number(self, value: Any) -> int:
        try:
            line_number = int(value)
        except (TypeError, ValueError):
            return 1
        return max(line_number, 1)

    def _severity(self, value: str | None) -> str:
        normalized = (value or "").upper()
        severity_map = {
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "ERROR": "HIGH",
            "MEDIUM": "MEDIUM",
            "WARNING": "MEDIUM",
            "WARN": "MEDIUM",
            "LOW": "LOW",
            "INFO": "LOW",
            "INFORMATIONAL": "LOW",
        }
        return severity_map.get(normalized, "LOW")
