import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.analysis.analysis_runner import EslintScanner, run_static_analysis
from app.services.analysis.bandit_scanner import BanditScanner
from app.services.analysis.base_scanner import ScannerResult
from app.services.analysis.gitleaks_scanner import GitleaksScanner
from app.services.analysis.ruff_scanner import RuffScanner
from app.services.analysis.semgrep_scanner import SemgrepScanner


class StaticAnalysisTest(unittest.TestCase):
    def test_semgrep_scanner_maps_results_to_unified_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = {
                "results": [
                    {
                        "check_id": "python.lang.security.audit",
                        "path": str(root / "app.py"),
                        "start": {"line": 7},
                        "extra": {
                            "message": "Avoid unsafe call.",
                            "severity": "ERROR",
                            "metadata": {"category": "security"},
                        },
                    }
                ]
            }

            with patch.object(SemgrepScanner, "_run_json_command", return_value=(payload, None)):
                result = SemgrepScanner().scan(root)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.findings[0]["severity"], "HIGH")
        self.assertEqual(result.findings[0]["category"], "security")
        self.assertEqual(result.findings[0]["filePath"], "app.py")
        self.assertEqual(result.findings[0]["lineNumber"], 7)
        self.assertEqual(result.findings[0]["toolName"], "semgrep")

    def test_bandit_scanner_allows_finding_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = {
                "results": [
                    {
                        "filename": str(root / "service.py"),
                        "line_number": 3,
                        "issue_severity": "HIGH",
                        "issue_text": "Use of assert detected.",
                        "test_name": "assert_used",
                        "more_info": "https://bandit.readthedocs.io/",
                    }
                ]
            }

            with patch.object(BanditScanner, "_run_json_command", return_value=(payload, None)):
                result = BanditScanner().scan(root)

        self.assertEqual(result.findings[0]["title"], "assert_used")
        self.assertEqual(result.findings[0]["severity"], "HIGH")
        self.assertEqual(result.findings[0]["toolName"], "bandit")

    def test_ruff_scanner_maps_lint_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = [
                {
                    "filename": str(root / "main.py"),
                    "location": {"row": 12},
                    "code": "F401",
                    "message": "Imported but unused.",
                }
            ]

            with patch.object(RuffScanner, "_run_json_command", return_value=(payload, None)):
                result = RuffScanner().scan(root)

        self.assertEqual(result.findings[0]["category"], "quality")
        self.assertEqual(result.findings[0]["title"], "F401")
        self.assertEqual(result.findings[0]["lineNumber"], 12)

    def test_gitleaks_scanner_maps_secret_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = [
                {
                    "File": str(root / ".env"),
                    "StartLine": 1,
                    "RuleID": "generic-api-key",
                    "Description": "Generic API key detected.",
                }
            ]

            with patch.object(GitleaksScanner, "_run_json_command", return_value=(payload, None)):
                result = GitleaksScanner().scan(root)

        self.assertEqual(result.findings[0]["severity"], "HIGH")
        self.assertEqual(result.findings[0]["category"], "secret")
        self.assertEqual(result.findings[0]["filePath"], ".env")

    def test_eslint_scanner_skips_repositories_without_package_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = EslintScanner().scan(Path(temp_dir))

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.findings, [])

    def test_eslint_scanner_runs_when_package_json_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text('{"scripts": {}}\n', encoding="utf-8")
            payload = [
                {
                    "filePath": str(root / "src" / "app.js"),
                    "messages": [
                        {
                            "ruleId": "no-unused-vars",
                            "severity": 2,
                            "message": "x is defined but never used.",
                            "line": 4,
                        }
                    ],
                }
            ]

            with patch.object(EslintScanner, "_run_json_command", return_value=(payload, None)):
                result = EslintScanner().scan(root)

        self.assertEqual(result.findings[0]["severity"], "HIGH")
        self.assertEqual(result.findings[0]["filePath"], "src/app.js")
        self.assertEqual(result.findings[0]["toolName"], "eslint")

    def test_runner_returns_sorted_findings_and_tool_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            results = [
                ScannerResult("semgrep", "completed", [{"filePath": "b.py", "lineNumber": 2, "toolName": "semgrep", "title": "B"}]),
                ScannerResult("bandit", "completed", [{"filePath": "a.py", "lineNumber": 1, "toolName": "bandit", "title": "A"}]),
                ScannerResult("ruff", "completed", []),
                ScannerResult("gitleaks", "completed", []),
                ScannerResult("eslint", "skipped", [], "package.json was not found."),
            ]

            with patch("app.services.analysis.analysis_runner.SemgrepScanner.scan", return_value=results[0]), \
                patch("app.services.analysis.analysis_runner.BanditScanner.scan", return_value=results[1]), \
                patch("app.services.analysis.analysis_runner.RuffScanner.scan", return_value=results[2]), \
                patch("app.services.analysis.analysis_runner.GitleaksScanner.scan", return_value=results[3]), \
                patch("app.services.analysis.analysis_runner.EslintScanner.scan", return_value=results[4]):
                analysis = run_static_analysis(root)

        self.assertEqual(analysis["totalFindings"], 2)
        self.assertEqual([finding["filePath"] for finding in analysis["findings"]], ["a.py", "b.py"])
        self.assertEqual(len(analysis["tools"]), 5)
        self.assertEqual(analysis["tools"][4]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
