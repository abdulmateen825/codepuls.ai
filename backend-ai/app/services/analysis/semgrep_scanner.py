from pathlib import Path

from app.services.analysis.base_scanner import BaseScanner, Finding, ScannerResult


class SemgrepScanner(BaseScanner):
    tool_name = "semgrep"
    category = "static-analysis"

    def scan(self, repository_path: Path) -> ScannerResult:
        data, error = self._run_json_command(
            ["semgrep", "--config", "auto", "--json", str(repository_path)],
            repository_path,
        )
        if error:
            return self._skipped(error)

        findings = []
        for result in data.get("results", []) if isinstance(data, dict) else []:
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})
            title = metadata.get("shortlink") or result.get("check_id") or "Semgrep finding"
            description = extra.get("message") or title
            recommendation = metadata.get("fix") or metadata.get("references") or "Review the Semgrep rule guidance and update the affected code."

            findings.append(
                Finding(
                    severity=self._severity(extra.get("severity")),
                    category=metadata.get("category") or self.category,
                    title=str(title),
                    description=str(description),
                    recommendation=str(recommendation),
                    filePath=self._relative_path(result.get("path"), repository_path),
                    lineNumber=self._line_number(result.get("start", {}).get("line")),
                    toolName=self.tool_name,
                )
            )

        return self._completed(findings)
