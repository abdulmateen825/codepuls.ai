from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.services.code_smells.base_detector import BaseCodeSmellDetector
from app.services.code_smells.models import CodeSmellFinding, DetectorResult, Severity, SmellType


class DuplicateCodeDetector(BaseCodeSmellDetector):
    detector_name = "duplicate-code-smells"
    supported_languages = {"python", "java", "javascript", "typescript", "javascriptreact", "typescriptreact"}

    def detect(self, repository_root: Path, parsed_files: list[dict[str, Any]]) -> DetectorResult:
        windows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        window_size = self.thresholds.min_duplicate_lines

        for parsed_file in parsed_files:
            if not self.supports(parsed_file.get("language")):
                continue

            file_path = str(parsed_file.get("path", ""))
            try:
                lines = (repository_root / file_path).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError as exception:
                return self.failed(f"Duplicate detector could not read {file_path}: {exception}", parsed_file.get("language"))

            normalized_lines = [_normalize_line(line) for line in lines]
            for index in range(0, max(0, len(normalized_lines) - window_size + 1)):
                window = normalized_lines[index:index + window_size]
                if not _is_meaningful_window(window):
                    continue
                digest = hashlib.sha256("\n".join(window).encode("utf-8")).hexdigest()
                windows[digest].append({
                    "filePath": file_path,
                    "language": str(parsed_file.get("language", "")).upper(),
                    "startLine": index + 1,
                    "endLine": index + window_size,
                })

        findings: list[CodeSmellFinding] = []
        seen_locations: set[tuple[str, int]] = set()
        for locations in windows.values():
            unique_locations = _unique_locations(locations)
            if len(unique_locations) < 2:
                continue

            for location in unique_locations:
                key = (location["filePath"], location["startLine"])
                if key in seen_locations:
                    continue
                seen_locations.add(key)
                findings.append(CodeSmellFinding(
                    ruleId=SmellType.DUPLICATED_CODE,
                    smellType=SmellType.DUPLICATED_CODE,
                    severity=Severity.MEDIUM,
                    language=location["language"],
                    filePath=location["filePath"],
                    startLine=location["startLine"],
                    endLine=location["endLine"],
                    title="Duplicated code block detected",
                    message=f"This {window_size}-line block appears in {len(unique_locations)} locations.",
                    evidence={
                        "duplicateLineCount": window_size,
                        "occurrenceCount": len(unique_locations),
                        "locations": unique_locations[:5],
                    },
                    metrics={"duplicateLineCount": window_size, "occurrenceCount": len(unique_locations)},
                    suggestedRefactoring="Extract shared logic into a reusable function or module",
                    confidence=0.88,
                ))

        return DetectorResult(detector=self.detector_name, status="completed", findings=findings)


def _normalize_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith(("#", "//", "*")):
        return ""
    return " ".join(stripped.split())


def _is_meaningful_window(lines: list[str]) -> bool:
    non_empty = [line for line in lines if line]
    return len(non_empty) == len(lines) and sum(len(line) for line in non_empty) >= 80


def _unique_locations(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, int]] = set()
    unique: list[dict[str, Any]] = []
    for location in locations:
        key = (location["filePath"], location["startLine"], location["endLine"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(location)
    return unique
