from pathlib import Path

from app.services.analysis.base_scanner import BaseScanner, Finding, ScannerResult


class GitleaksScanner(BaseScanner):
    tool_name = "gitleaks"
    category = "secret"

    def scan(self, repository_path: Path) -> ScannerResult:
        data, error = self._run_json_command(
            [
                "gitleaks",
                "detect",
                "--source",
                str(repository_path),
                "--report-format",
                "json",
                "--no-git",
            ],
            repository_path,
            allowed_finding_exit_codes={1},
        )
        if error:
            return self._skipped(error)

        findings = []
        for result in data if isinstance(data, list) else []:
            rule_id = result.get("RuleID") or "Potential secret"
            description = result.get("Description") or rule_id

            findings.append(
                Finding(
                    severity="HIGH",
                    category=self.category,
                    title=str(rule_id),
                    description=str(description),
                    recommendation="Revoke the exposed credential, rotate affected secrets, and remove the secret from source history.",
                    filePath=self._relative_path(result.get("File"), repository_path),
                    lineNumber=self._line_number(result.get("StartLine")),
                    toolName=self.tool_name,
                )
            )

        return self._completed(findings)
