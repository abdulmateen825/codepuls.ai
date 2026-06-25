from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.services.code_smells.config import CodeSmellThresholds
from app.services.code_smells.models import DetectorResult, DetectorWarning


class BaseCodeSmellDetector(ABC):
    detector_name: str
    supported_languages: set[str]

    def __init__(self, thresholds: CodeSmellThresholds) -> None:
        self.thresholds = thresholds

    def supports(self, language: str | None) -> bool:
        return bool(language) and language.lower() in self.supported_languages

    @abstractmethod
    def detect(self, repository_root: Path, parsed_files: list[dict[str, Any]]) -> DetectorResult:
        raise NotImplementedError

    def skipped(self, message: str, language: str | None = None) -> DetectorResult:
        return DetectorResult(
            detector=self.detector_name,
            status="skipped",
            findings=[],
            warnings=[
                DetectorWarning(
                    detector=self.detector_name,
                    language=language,
                    message=message,
                )
            ],
        )

    def failed(self, message: str, language: str | None = None) -> DetectorResult:
        return DetectorResult(
            detector=self.detector_name,
            status="failed",
            findings=[],
            warnings=[
                DetectorWarning(
                    detector=self.detector_name,
                    language=language,
                    message=message,
                )
            ],
        )
