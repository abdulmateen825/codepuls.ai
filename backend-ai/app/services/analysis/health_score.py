from collections import Counter
from typing import Iterable


SEVERITY_PENALTIES = {
    "CRITICAL": 10,
    "HIGH": 5,
    "MEDIUM": 2,
    "LOW": 1,
}

DIMENSION_RULES = {
    "securityScore": {
        "categories": {"security", "secret"},
        "tools": {"bandit", "gitleaks"},
        "keywords": {"auth", "credential", "password", "secret", "security", "token", "vulnerability"},
        "cleanReason": "No security risks detected.",
    },
    "maintainabilityScore": {
        "categories": {"maintainability", "quality", "static-analysis"},
        "tools": {"eslint", "ruff"},
        "keywords": {"complex", "duplication", "lint", "maintainability", "unused"},
        "cleanReason": "No maintainability risks detected.",
    },
    "architectureScore": {
        "categories": {"architecture"},
        "tools": set(),
        "keywords": {"architecture", "circular", "coupling", "dependency", "layer", "module"},
        "cleanReason": "No architecture risks detected.",
    },
    "performanceScore": {
        "categories": {"performance"},
        "tools": set(),
        "keywords": {"cache", "memory", "n+1", "performance", "query", "slow", "timeout"},
        "cleanReason": "No performance risks detected.",
    },
}


def calculate_health_scores(findings: list[dict]) -> dict:
    return {
        "overallScore": _score_dimension(findings, "overall", findings),
        "securityScore": _score_dimension(findings, "security", _matching_findings(findings, "securityScore")),
        "maintainabilityScore": _score_dimension(findings, "maintainability", _matching_findings(findings, "maintainabilityScore")),
        "architectureScore": _score_dimension(findings, "architecture", _matching_findings(findings, "architectureScore")),
        "performanceScore": _score_dimension(findings, "performance", _matching_findings(findings, "performanceScore")),
    }


def spring_score_summary(health_scores: dict) -> dict:
    return {
        "qualityScore": health_scores["overallScore"]["score"],
        "securityScore": health_scores["securityScore"]["score"],
        "maintainabilityScore": health_scores["maintainabilityScore"]["score"],
    }


def _score_dimension(all_findings: list[dict], label: str, findings: Iterable[dict]) -> dict:
    scoped_findings = list(findings)
    score = max(0, 100 - sum(_penalty(finding) for finding in scoped_findings))

    return {
        "score": score,
        "grade": _grade(score),
        "reasons": _reasons(label, scoped_findings),
        "topRisks": _top_risks(scoped_findings or all_findings),
    }


def _matching_findings(findings: list[dict], score_key: str) -> list[dict]:
    rules = DIMENSION_RULES[score_key]

    return [
        finding
        for finding in findings
        if _normalized(finding.get("category")) in rules["categories"]
        or _normalized(finding.get("toolName")) in rules["tools"]
        or any(keyword in _search_text(finding) for keyword in rules["keywords"])
    ]


def _penalty(finding: dict) -> int:
    severity = str(finding.get("severity", "")).upper()
    return SEVERITY_PENALTIES.get(severity, SEVERITY_PENALTIES["LOW"])


def _grade(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Average"
    return "Poor"


def _reasons(label: str, findings: list[dict]) -> list[str]:
    if not findings:
        if label == "overall":
            return ["No findings detected."]
        return [DIMENSION_RULES[f"{label}Score"]["cleanReason"]]

    counts = Counter(str(finding.get("severity", "LOW")).upper() for finding in findings)
    reasons = []
    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = counts.get(severity, 0)
        if count:
            penalty = SEVERITY_PENALTIES[severity] * count
            issue_word = "issue" if count == 1 else "issues"
            reasons.append(f"{count} {severity.lower()} {issue_word} (-{penalty})")

    return reasons


def _top_risks(findings: Iterable[dict]) -> list[dict]:
    sorted_findings = sorted(
        findings,
        key=lambda finding: (
            -SEVERITY_PENALTIES.get(str(finding.get("severity", "")).upper(), 1),
            str(finding.get("filePath", "")),
            int(finding.get("lineNumber") or 1),
        ),
    )

    return [
        {
            "severity": str(finding.get("severity", "LOW")).upper(),
            "title": str(finding.get("title", "Finding")),
            "filePath": str(finding.get("filePath", "")),
            "lineNumber": int(finding.get("lineNumber") or 1),
            "toolName": str(finding.get("toolName", "")),
        }
        for finding in sorted_findings[:5]
    ]


def _search_text(finding: dict) -> str:
    return " ".join(
        str(finding.get(key, ""))
        for key in ("category", "title", "description", "recommendation", "toolName")
    ).lower()


def _normalized(value: object) -> str:
    return str(value or "").strip().lower()
