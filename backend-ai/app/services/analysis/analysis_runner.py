from pathlib import Path

from app.services.analysis.bandit_scanner import BanditScanner
from app.services.analysis.base_scanner import BaseScanner, Finding, ScannerResult
from app.services.analysis.gitleaks_scanner import GitleaksScanner
from app.services.analysis.ruff_scanner import RuffScanner
from app.services.analysis.semgrep_scanner import SemgrepScanner


class EslintScanner(BaseScanner):
    tool_name = "eslint"
    category = "quality"

    def scan(self, repository_path: Path) -> ScannerResult:
        if not (repository_path / "package.json").exists():
            return ScannerResult(
                toolName=self.tool_name,
                status="skipped",
                findings=[],
                error="package.json was not found.",
            )

        data, error = self._run_json_command(
            ["npx", "eslint", ".", "--format", "json"],
            repository_path,
            allowed_finding_exit_codes={1},
        )
        if error:
            return self._skipped(error)

        findings = []
        for file_result in data if isinstance(data, list) else []:
            file_path = file_result.get("filePath")
            for message in file_result.get("messages", []):
                title = message.get("ruleId") or "ESLint finding"
                findings.append(
                    Finding(
                        severity="HIGH" if message.get("severity") == 2 else "MEDIUM",
                        category=self.category,
                        title=str(title),
                        description=str(message.get("message") or title),
                        recommendation="Run ESLint locally and apply the rule-specific remediation.",
                        filePath=self._relative_path(file_path, repository_path),
                        lineNumber=self._line_number(message.get("line")),
                        toolName=self.tool_name,
                    )
                )

        return self._completed(findings)


def run_static_analysis(repository_path: Path) -> dict:
    scanners: list[BaseScanner] = [
        SemgrepScanner(),
        BanditScanner(),
        RuffScanner(),
        GitleaksScanner(),
        EslintScanner(),
    ]

    tool_results = [scanner.scan(repository_path) for scanner in scanners]
    findings = [
        finding
        for result in tool_results
        for finding in result.findings
    ]

    findings.sort(key=lambda item: (item["filePath"], item["lineNumber"], item["toolName"], item["title"]))

    return {
        "totalFindings": len(findings),
        "findings": findings,
        "tools": [result.to_dict() for result in tool_results],
    }
