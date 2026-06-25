import os
import unittest

from app.services.code_smells.config import load_thresholds
from app.services.code_smells.models import CodeSmellFinding, DetectorResult, SmellType


class CodeSmellModelsTest(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("CODE_SMELL_MAX_METHOD_LINES", None)

    def test_code_smell_finding_validates_line_range_and_callback_payload(self) -> None:
        finding = CodeSmellFinding(
            ruleId="LONG_METHOD",
            smellType="LONG_METHOD",
            severity="MEDIUM",
            language="JAVA",
            filePath="src/main/java/App.java",
            startLine=10,
            endLine=80,
            title="Method process is too long",
            message="The method contains 71 lines.",
            evidence={"lineCount": 71},
            metrics={"lineCount": 71},
            suggestedRefactoring="Extract Method",
            confidence=0.94,
        )

        payload = finding.to_callback_finding()

        self.assertEqual(payload["category"], "CODE_SMELL")
        self.assertEqual(payload["ruleId"], "LONG_METHOD")
        self.assertEqual(payload["smellType"], "LONG_METHOD")
        self.assertEqual(payload["lineNumber"], 10)
        self.assertEqual(payload["toolName"], "code-smell")

    def test_code_smell_finding_rejects_unknown_smell_type(self) -> None:
        with self.assertRaises(ValueError):
            CodeSmellFinding(
                ruleId="UNKNOWN",
                smellType="UNKNOWN",
                severity="MEDIUM",
                language="PYTHON",
                filePath="app.py",
                startLine=1,
                endLine=2,
                title="Unknown",
                message="Unknown smell.",
                confidence=0.5,
            )

    def test_code_smell_finding_rejects_invalid_confidence(self) -> None:
        with self.assertRaises(ValueError):
            CodeSmellFinding(
                ruleId=SmellType.LONG_METHOD,
                smellType=SmellType.LONG_METHOD,
                severity="MEDIUM",
                language="PYTHON",
                filePath="app.py",
                startLine=1,
                endLine=2,
                title="Invalid confidence",
                message="Confidence is invalid.",
                confidence=1.5,
            )

    def test_detector_result_normalizes_valid_status(self) -> None:
        result = DetectorResult(detector="python-smells", status="COMPLETED")

        self.assertEqual(result.status, "completed")

    def test_thresholds_are_configurable_and_fallback_to_defaults(self) -> None:
        os.environ["CODE_SMELL_MAX_METHOD_LINES"] = "75"

        thresholds = load_thresholds()

        self.assertEqual(thresholds.max_method_lines, 75)

        os.environ["CODE_SMELL_MAX_METHOD_LINES"] = "not-a-number"

        thresholds = load_thresholds()

        self.assertEqual(thresholds.max_method_lines, 50)


if __name__ == "__main__":
    unittest.main()
