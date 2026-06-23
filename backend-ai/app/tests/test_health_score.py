import unittest

from app.services.analysis.health_score import calculate_health_scores, spring_score_summary


class HealthScoreTest(unittest.TestCase):
    def test_empty_findings_returns_excellent_scores(self) -> None:
        scores = calculate_health_scores([])

        for score in scores.values():
            self.assertEqual(score["score"], 100)
            self.assertEqual(score["grade"], "Excellent")
            self.assertEqual(score["topRisks"], [])

    def test_overall_score_applies_required_severity_penalties(self) -> None:
        findings = [
            finding("CRITICAL", "security", "Hardcoded token", "app.py"),
            finding("HIGH", "quality", "Unused import", "main.py"),
            finding("MEDIUM", "performance", "Slow query", "repo.py"),
            finding("LOW", "architecture", "Layer warning", "service.py"),
        ]

        scores = calculate_health_scores(findings)

        self.assertEqual(scores["overallScore"]["score"], 82)
        self.assertEqual(scores["overallScore"]["grade"], "Good")
        self.assertEqual(
            scores["overallScore"]["reasons"],
            [
                "1 critical issue (-10)",
                "1 high issue (-5)",
                "1 medium issue (-2)",
                "1 low issue (-1)",
            ],
        )

    def test_grades_follow_required_ranges(self) -> None:
        self.assertEqual(calculate_health_scores([finding("LOW", "quality", "Low", "a.py")])["overallScore"]["grade"], "Excellent")
        self.assertEqual(calculate_health_scores([finding("CRITICAL", "quality", "Critical", "a.py"), finding("HIGH", "quality", "High", "b.py")])["overallScore"]["grade"], "Good")
        self.assertEqual(calculate_health_scores([finding("CRITICAL", "quality", "Critical", "a.py") for _ in range(3)])["overallScore"]["grade"], "Average")
        self.assertEqual(calculate_health_scores([finding("CRITICAL", "quality", "Critical", "a.py") for _ in range(5)])["overallScore"]["grade"], "Poor")

    def test_dimension_scores_use_matching_findings(self) -> None:
        findings = [
            finding("HIGH", "security", "Hardcoded password", ".env", tool_name="gitleaks"),
            finding("HIGH", "quality", "Unused import", "app.py", tool_name="ruff"),
            finding("MEDIUM", "architecture", "Circular dependency", "graph.py"),
            finding("LOW", "performance", "Slow query", "repo.py"),
        ]

        scores = calculate_health_scores(findings)

        self.assertEqual(scores["securityScore"]["score"], 95)
        self.assertEqual(scores["maintainabilityScore"]["score"], 95)
        self.assertEqual(scores["architectureScore"]["score"], 98)
        self.assertEqual(scores["performanceScore"]["score"], 99)

    def test_top_risks_are_sorted_by_severity(self) -> None:
        scores = calculate_health_scores([
            finding("LOW", "quality", "Low", "a.py"),
            finding("CRITICAL", "security", "Critical", "b.py"),
            finding("HIGH", "quality", "High", "c.py"),
        ])

        top_risks = scores["overallScore"]["topRisks"]

        self.assertEqual([risk["severity"] for risk in top_risks], ["CRITICAL", "HIGH", "LOW"])
        self.assertEqual(top_risks[0]["title"], "Critical")

    def test_spring_score_summary_maps_existing_score_fields(self) -> None:
        health_scores = calculate_health_scores([
            finding("HIGH", "security", "Token leak", ".env"),
            finding("LOW", "quality", "Lint", "app.py"),
        ])

        summary = spring_score_summary(health_scores)

        self.assertEqual(summary["qualityScore"], health_scores["overallScore"]["score"])
        self.assertEqual(summary["securityScore"], health_scores["securityScore"]["score"])
        self.assertEqual(summary["maintainabilityScore"], health_scores["maintainabilityScore"]["score"])


def finding(
    severity: str,
    category: str,
    title: str,
    file_path: str,
    tool_name: str = "semgrep",
) -> dict:
    return {
        "severity": severity,
        "category": category,
        "title": title,
        "description": title,
        "recommendation": "Review and fix.",
        "filePath": file_path,
        "lineNumber": 1,
        "toolName": tool_name,
    }


if __name__ == "__main__":
    unittest.main()
