from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.code_smells.config import CodeSmellThresholds, load_thresholds
from app.services.code_smells.duplicate_detector import DuplicateCodeDetector
from app.services.code_smells.models import DetectorResult, DetectorWarning
from app.services.code_smells.python_detector import PythonCodeSmellDetector
from app.services.code_smells.structure_detector import StructureCodeSmellDetector
from app.services.code_smells.source_extractor import SourceExtractionError, SourceExtractor


def run_code_smell_detection(
    repository_root: Path,
    parsed_repository: dict[str, Any],
    thresholds: CodeSmellThresholds | None = None,
) -> dict[str, Any]:
    thresholds = thresholds or load_thresholds()
    parsed_files = list(parsed_repository.get("files", []))
    detectors = [
        PythonCodeSmellDetector(thresholds),
        StructureCodeSmellDetector(thresholds),
        DuplicateCodeDetector(thresholds),
    ]

    results: list[DetectorResult] = []
    for detector in detectors:
        try:
            results.append(detector.detect(repository_root, parsed_files))
        except Exception as exception:
            results.append(DetectorResult(
                detector=detector.detector_name,
                status="failed",
                warnings=[
                    DetectorWarning(
                        detector=detector.detector_name,
                        message=str(exception)[:500] or "Detector failed.",
                    )
                ],
            ))

    warnings = [
        warning.model_dump()
        for result in results
        for warning in result.warnings
    ]
    extractor = SourceExtractor(thresholds)
    findings = []
    for result in results:
        for finding in result.findings:
            callback_finding = finding.to_callback_finding()
            try:
                context = extractor.extract(
                    repository_root,
                    callback_finding["filePath"],
                    callback_finding["startLine"],
                    callback_finding["endLine"],
                )
                callback_finding["codeSnippet"] = context.code_snippet
                callback_finding["contextBefore"] = context.context_before
                callback_finding["contextAfter"] = context.context_after
                callback_finding["startLine"] = context.actual_start_line
                callback_finding["endLine"] = context.actual_end_line
                callback_finding["sourceTruncated"] = context.truncated
            except SourceExtractionError as exception:
                callback_finding["sourceTruncated"] = True
                warnings.append({
                    "detector": result.detector,
                    "language": callback_finding.get("language"),
                    "message": f"Source extraction failed for {callback_finding['filePath']}: {exception}",
                })
            findings.append(callback_finding)

    findings = _deduplicate(findings)
    findings.sort(key=lambda item: (item["filePath"], item["startLine"], item["ruleId"], item["title"]))

    return {
        "totalFindings": len(findings),
        "findings": findings,
        "detectors": [
            {
                "detector": result.detector,
                "status": result.status,
                "findingCount": len(result.findings),
                "warnings": [warning.model_dump() for warning in result.warnings],
            }
            for result in results
        ],
        "warnings": warnings,
        "summary": _summary(findings),
    }


def _deduplicate(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, int, int, str]] = set()
    unique: list[dict[str, Any]] = []
    for finding in findings:
        key = (
            str(finding.get("category", "")),
            str(finding.get("ruleId", "")),
            str(finding.get("filePath", "")),
            int(finding.get("startLine") or finding.get("lineNumber") or 1),
            int(finding.get("endLine") or finding.get("lineNumber") or 1),
            str(finding.get("title", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def _summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_smell_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_language: dict[str, int] = {}

    for finding in findings:
        _increment(by_smell_type, str(finding.get("smellType", "UNKNOWN")))
        _increment(by_severity, str(finding.get("severity", "LOW")).upper())
        _increment(by_language, str(finding.get("language", "UNKNOWN")).upper())

    return {
        "totalSmells": len(findings),
        "bySmellType": by_smell_type,
        "bySeverity": by_severity,
        "byLanguage": by_language,
    }


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1
