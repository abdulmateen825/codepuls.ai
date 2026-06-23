from pathlib import Path

from app.services.analysis.base_scanner import BaseScanner, Finding, ScannerResult


class RuffScanner(BaseScanner):
    tool_name = "ruff"
    category = "quality"

    def scan(self, repository_path: Path) -> ScannerResult:
        data, error = self._run_json_command(
            ["ruff", "check", str(repository_path), "--output-format", "json"],
            repository_path,
            allowed_finding_exit_codes={1},
        )
        if error:
            return self._skipped(error)

        findings = []
        for result in data if isinstance(data, list) else []:
            code = result.get("code") or "Ruff"
            message = result.get("message") or "Ruff lint finding"

            findings.append(
                Finding(
                    severity="MEDIUM",
                    category=self.category,
                    title=str(code),
                    description=str(message),
                    recommendation="Run Ruff locally and apply the suggested lint or formatting correction.",
                    filePath=self._relative_path(result.get("filename"), repository_path),
                    lineNumber=self._line_number(result.get("location", {}).get("row")),
                    toolName=self.tool_name,
                )
            )

        return self._completed(findings)
