from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.code_smells.config import CodeSmellThresholds, load_thresholds
from app.services.code_smells.duplicate_detector import DuplicateCodeDetector
from app.services.code_smells.models import DetectorResult, DetectorWarning
from app.services.code_smells.python_detector import PythonCodeSmellDetector
from app.services.code_smells.structure_detector import StructureCodeSmellDetector


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

    findings = [
        finding.to_callback_finding()
        for result in results
        for finding in result.findings
    ]
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
        "warnings": [
            warning.model_dump()
            for result in results
            for warning in result.warnings
        ],
    }
