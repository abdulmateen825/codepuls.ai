import unittest
from unittest.mock import patch
from uuid import UUID

from app.schemas.internal_analysis import AnalyzeRequest
from app.services.analysis.scan_worker import process_scan


class ScanCallbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.request = AnalyzeRequest(
            scanId=UUID("11111111-1111-1111-1111-111111111111"),
            repositoryId=UUID("22222222-2222-2222-2222-222222222222"),
            githubUrl="https://github.com/codepulse/backend-core",
            branch="main",
        )

    def test_process_scan_sends_running_and_completed_callbacks(self) -> None:
        repository_metadata = {
            "fileTree": {"name": "repo", "children": []},
            "parsedFiles": {"totalFiles": 1, "files": []},
            "analysis": {
                "totalFindings": 1,
                "tools": [{"toolName": "ruff", "status": "completed", "findingCount": 1}],
                "findings": [
                    {
                        "severity": "HIGH",
                        "category": "quality",
                        "title": "F401",
                        "description": "Unused import.",
                        "recommendation": "Remove it.",
                        "filePath": "app.py",
                        "lineNumber": 1,
                        "toolName": "ruff",
                    }
                ],
            },
        }

        with patch("app.services.analysis.scan_worker.prepare_repository_for_scan", return_value=repository_metadata), \
                patch("app.services.analysis.scan_worker.send_scan_results") as send_scan_results:
            process_scan(self.request)

        self.assertEqual(send_scan_results.call_count, 2)
        running_payload = send_scan_results.call_args_list[0].args[1]
        completed_payload = send_scan_results.call_args_list[1].args[1]
        self.assertEqual(running_payload["status"], "RUNNING")
        self.assertEqual(completed_payload["status"], "COMPLETED")
        self.assertEqual(completed_payload["findings"][0]["toolName"], "ruff")
        self.assertEqual(completed_payload["scores"]["qualityScore"], 95)
        self.assertEqual(completed_payload["scores"]["maintainabilityScore"], 95)
        self.assertEqual(completed_payload["metadata"]["totalFindings"], 1)
        self.assertEqual(completed_payload["metadata"]["healthScores"]["overallScore"]["grade"], "Excellent")

    def test_process_scan_sends_failed_callback_when_scan_work_raises(self) -> None:
        with patch("app.services.analysis.scan_worker.prepare_repository_for_scan", side_effect=ValueError("clone failed")), \
                patch("app.services.analysis.scan_worker.logger.exception"), \
                patch("app.services.analysis.scan_worker.send_scan_results") as send_scan_results:
            process_scan(self.request)

        self.assertEqual(send_scan_results.call_count, 2)
        failed_payload = send_scan_results.call_args_list[1].args[1]
        self.assertEqual(failed_payload["status"], "FAILED")
        self.assertEqual(failed_payload["errorMessage"], "clone failed")


if __name__ == "__main__":
    unittest.main()
