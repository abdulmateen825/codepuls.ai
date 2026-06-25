import os
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.report_generation import GenerateReportRequest
from app.services.reports.pdf_generator import generate_scan_report_pdf


class ReportsTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["INTERNAL_API_KEY"] = "test-key"
        self.client = TestClient(app)
        self.payload = {
            "scanId": "11111111-1111-1111-1111-111111111111",
            "repositoryId": "22222222-2222-2222-2222-222222222222",
            "repositoryFullName": "codepulse/backend-core",
            "repositoryUrl": "https://github.com/codepulse/backend-core",
            "status": "COMPLETED",
            "qualityScore": 92,
            "securityScore": 88,
            "maintainabilityScore": 90,
            "findings": [
                {
                    "severity": "HIGH",
                    "category": "security",
                    "title": "Hardcoded secret",
                    "description": "A hardcoded secret was detected.",
                    "recommendation": "Move the secret into managed configuration.",
                    "filePath": "src/App.java",
                    "lineNumber": 42,
                    "ruleId": "gitleaks:generic-api-key",
                }
            ],
        }

    def test_generate_scan_report_pdf_returns_pdf_bytes(self) -> None:
        pdf = generate_scan_report_pdf(GenerateReportRequest(**self.payload))

        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        self.assertIn(b"%%EOF", pdf)

    def test_internal_report_endpoint_requires_api_key(self) -> None:
        response = self.client.post(
            "/internal/reports/pdf",
            json=self.payload,
            headers={"Authorization": "Bearer wrong"},
        )

        self.assertEqual(response.status_code, 401)

    def test_internal_report_endpoint_returns_pdf(self) -> None:
        response = self.client.post(
            "/internal/reports/pdf",
            json=self.payload,
            headers={"Authorization": "Bearer test-key"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-1.4"))


if __name__ == "__main__":
    unittest.main()
