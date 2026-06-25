import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from app.schemas.internal_analysis import AnalyzeRequest
from app.services.analysis.scan_worker import prepare_repository_for_scan, process_scan
from app.services.code_smells.config import CodeSmellThresholds


class CodeSmellPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.request = AnalyzeRequest(
            scanId=UUID("11111111-1111-1111-1111-111111111111"),
            repositoryId=UUID("22222222-2222-2222-2222-222222222222"),
            githubUrl="https://github.com/codepulse/backend-core",
            branch="main",
        )

    def test_prepare_repository_merges_code_smells_and_cleans_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text(
                "def process(a, b, c):\n"
                "    if a:\n"
                "        if b:\n"
                "            if c:\n"
                "                return c\n"
                "    return None\n",
                encoding="utf-8",
            )

            with patch("app.services.analysis.scan_worker.clone_public_repository", return_value=root), \
                    patch("app.services.analysis.scan_worker.run_static_analysis", return_value={"totalFindings": 0, "findings": [], "tools": []}), \
                    patch("app.services.analysis.scan_worker._index_rag_chunks", return_value={"status": "skipped"}), \
                    patch("app.services.analysis.scan_worker.cleanup_repository") as cleanup_repository, \
                    patch("app.services.code_smells.runner.load_thresholds", return_value=CodeSmellThresholds(
                        max_cyclomatic_complexity=2,
                        max_nesting_depth=2,
                        max_parameter_count=2,
                    )):
                metadata = prepare_repository_for_scan(self.request)

        cleanup_repository.assert_called_once_with(root)
        findings = metadata["analysis"]["findings"]
        smell_types = {finding["smellType"] for finding in findings}

        self.assertIn("HIGH_CYCLOMATIC_COMPLEXITY", smell_types)
        self.assertIn("DEEP_NESTING", smell_types)
        self.assertIn("LONG_PARAMETER_LIST", smell_types)
        self.assertEqual(metadata["codeSmells"]["summary"]["totalSmells"], len(findings))
        self.assertTrue(findings[0]["codeSnippet"])

    def test_process_scan_includes_code_smell_metadata_and_scores(self) -> None:
        repository_metadata = {
            "fileTree": {"name": "repo", "children": []},
            "parsedFiles": {"totalFiles": 1, "files": []},
            "analysis": {
                "totalFindings": 1,
                "tools": [{"toolName": "code-smell", "status": "completed", "findingCount": 1}],
                "findings": [
                    {
                        "severity": "MEDIUM",
                        "category": "CODE_SMELL",
                        "ruleId": "LONG_METHOD",
                        "smellType": "LONG_METHOD",
                        "title": "Long method",
                        "description": "Method is too long.",
                        "recommendation": "Extract Method",
                        "filePath": "app.py",
                        "lineNumber": 1,
                        "startLine": 1,
                        "endLine": 10,
                        "toolName": "code-smell",
                    }
                ],
            },
            "codeSmells": {
                "summary": {
                    "totalSmells": 1,
                    "bySmellType": {"LONG_METHOD": 1},
                    "bySeverity": {"MEDIUM": 1},
                    "byLanguage": {"PYTHON": 1},
                },
                "detectors": [],
                "warnings": [],
            },
            "ragIndex": {"status": "skipped"},
        }

        with patch("app.services.analysis.scan_worker.prepare_repository_for_scan", return_value=repository_metadata), \
                patch("app.services.analysis.scan_worker.send_scan_results") as send_scan_results:
            process_scan(self.request)

        completed_payload = send_scan_results.call_args_list[1].args[1]

        self.assertEqual(completed_payload["status"], "COMPLETED")
        self.assertEqual(completed_payload["metadata"]["codeSmells"]["totalSmells"], 1)
        self.assertEqual(completed_payload["metadata"]["codeSmells"]["bySmellType"]["LONG_METHOD"], 1)
        self.assertEqual(completed_payload["scores"]["maintainabilityScore"], 98)


if __name__ == "__main__":
    unittest.main()
