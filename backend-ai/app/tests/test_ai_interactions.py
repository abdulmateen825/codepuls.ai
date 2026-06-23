import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai_interactions import FindingExplainRequest
from app.services.llm.finding_explainer import explain_finding


class AiInteractionsTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["INTERNAL_API_KEY"] = "test-key"
        self.client = TestClient(app)

    def test_repository_chat_requires_internal_api_key(self) -> None:
        response = self.client.post(
            "/internal/repositories/chat",
            json={
                "repositoryId": "22222222-2222-2222-2222-222222222222",
                "question": "Where is auth?",
                "history": [],
            },
            headers={"Authorization": "Bearer wrong"},
        )

        self.assertEqual(response.status_code, 401)

    def test_repository_chat_returns_answer_and_references(self) -> None:
        with patch(
            "app.api.internal.answer_repository_question",
            return_value={
                "answer": "### Auth\nJWT lives in backend-core.",
                "fileReferences": [
                    {
                        "filePath": "src/auth.py",
                        "startLine": 1,
                        "endLine": 10,
                        "symbolName": "AuthService",
                        "score": 0.9,
                    }
                ],
                "suggestedQuestions": ["How are tokens refreshed?"],
            },
        ):
            response = self.client.post(
                "/internal/repositories/chat",
                json={
                    "repositoryId": "22222222-2222-2222-2222-222222222222",
                    "question": "Where is auth?",
                    "history": [],
                },
                headers={"Authorization": "Bearer test-key"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["fileReferences"][0]["filePath"], "src/auth.py")
        self.assertEqual(response.json()["suggestedQuestions"], ["How are tokens refreshed?"])

    def test_finding_explanation_uses_nearby_code_context(self) -> None:
        scan_id = UUID("11111111-1111-1111-1111-111111111111")
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / str(scan_id)
            workspace.mkdir()
            (workspace / "app.py").write_text("import os\n\nprint(os.getcwd())\n", encoding="utf-8")

            with patch("app.services.llm.finding_explainer.scan_workspace", return_value=workspace):
                response = explain_finding(
                    FindingExplainRequest(
                        repositoryId=UUID("22222222-2222-2222-2222-222222222222"),
                        scanId=scan_id,
                        findingId=UUID("33333333-3333-3333-3333-333333333333"),
                        severity="HIGH",
                        category="quality",
                        title="Unused import",
                        description="Import is unused.",
                        recommendation="Remove the import.",
                        filePath="app.py",
                        lineNumber=1,
                        ruleId="ruff:F401",
                    )
                )

        self.assertIn("Unused import", response["summary"])
        self.assertEqual(response["fileReferences"][0]["filePath"], "app.py")
        self.assertGreaterEqual(response["confidenceScore"], 0)


if __name__ == "__main__":
    unittest.main()
