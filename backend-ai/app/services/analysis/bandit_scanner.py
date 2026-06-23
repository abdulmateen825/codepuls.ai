from pathlib import Path

from app.services.analysis.base_scanner import BaseScanner, Finding, ScannerResult


class BanditScanner(BaseScanner):
    tool_name = "bandit"
    category = "security"

    def scan(self, repository_path: Path) -> ScannerResult:
        data, error = self._run_json_command(
            ["bandit", "-r", str(repository_path), "-f", "json", "-q"],
            repository_path,
            allowed_finding_exit_codes={1},
        )
        if error:
            return self._skipped(error)

        findings = []
        for result in data.get("results", []) if isinstance(data, dict) else []:
            test_name = result.get("test_name") or result.get("test_id") or "Bandit finding"
            description = result.get("issue_text") or test_name
            recommendation = result.get("more_info") or "Review the Bandit security guidance and apply the recommended mitigation."

            findings.append(
                Finding(
                    severity=self._severity(result.get("issue_severity")),
                    category=self.category,
                    title=str(test_name),
                    description=str(description),
                    recommendation=str(recommendation),
                    filePath=self._relative_path(result.get("filename"), repository_path),
                    lineNumber=self._line_number(result.get("line_number")),
                    toolName=self.tool_name,
                )
            )

        return self._completed(findings)
