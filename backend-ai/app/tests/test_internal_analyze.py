import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class InternalAnalyzeTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["INTERNAL_API_KEY"] = "test-key"
        self.client = TestClient(app)
        self.payload = {
            "scanId": "11111111-1111-1111-1111-111111111111",
            "repositoryId": "22222222-2222-2222-2222-222222222222",
            "githubUrl": "https://github.com/codepulse/backend-core",
            "branch": "main",
        }

    def test_analyze_returns_accepted_response_with_file_tree(self) -> None:
        file_tree = {
            "name": "backend-core",
            "path": "",
            "type": "directory",
            "children": [],
        }
        parsed_files = {
            "totalFiles": 0,
            "files": [],
        }
        analysis = {
            "totalFindings": 0,
            "findings": [],
            "tools": [],
        }

        with patch(
            "app.api.internal.prepare_repository_for_scan",
            return_value={"fileTree": file_tree, "parsedFiles": parsed_files, "analysis": analysis},
        ):
            response = self.client.post(
                "/internal/analyze",
                json=self.payload,
                headers={"Authorization": "Bearer test-key"},
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {
                "accepted": True,
                "scanId": self.payload["scanId"],
                "status": "accepted",
                "fileTree": file_tree,
                "parsedFiles": parsed_files,
                "analysis": analysis,
            },
        )

    def test_analyze_rejects_invalid_internal_api_key(self) -> None:
        response = self.client.post(
            "/internal/analyze",
            json=self.payload,
            headers={"Authorization": "Bearer wrong"},
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
