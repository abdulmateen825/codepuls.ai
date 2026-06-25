from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.services.code_smells.config import CodeSmellThresholds
from app.services.code_smells.models import SourceContext


class SourceExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class SourceExtractor:
    thresholds: CodeSmellThresholds

    def extract(
        self,
        repository_root: Path,
        relative_file_path: str,
        start_line: int,
        end_line: int,
        context_lines: int | None = None,
    ) -> SourceContext:
        if start_line <= 0:
            raise SourceExtractionError("startLine must be greater than zero.")
        if end_line < start_line:
            raise SourceExtractionError("endLine must be greater than or equal to startLine.")

        root = repository_root.resolve()
        file_path = self._safe_file_path(root, relative_file_path)
        self._validate_file(file_path)

        lines = self._read_lines(file_path)
        if not lines:
            raise SourceExtractionError("Cannot extract source from an empty file.")

        requested_context = self.thresholds.context_lines if context_lines is None else max(0, context_lines)
        actual_start = min(start_line, len(lines))
        actual_end = min(end_line, len(lines))
        extraction_start = max(1, actual_start - requested_context)
        extraction_end = min(len(lines), actual_end + requested_context)

        truncated = False
        if actual_end - actual_start + 1 > self.thresholds.max_snippet_lines:
            actual_end = actual_start + self.thresholds.max_snippet_lines - 1
            extraction_end = min(len(lines), actual_end + requested_context)
            truncated = True

        context_before = "\n".join(lines[extraction_start - 1:actual_start - 1])
        code_snippet = "\n".join(lines[actual_start - 1:actual_end])
        context_after = "\n".join(lines[actual_end:extraction_end])

        code_snippet, snippet_truncated = self._limit_chars(code_snippet)
        context_before, before_truncated = self._limit_chars(context_before)
        context_after, after_truncated = self._limit_chars(context_after)

        return SourceContext(
            codeSnippet=code_snippet,
            contextBefore=context_before,
            contextAfter=context_after,
            actualStartLine=actual_start,
            actualEndLine=actual_end,
            truncated=truncated or snippet_truncated or before_truncated or after_truncated,
        )

    def _safe_file_path(self, root: Path, relative_file_path: str) -> Path:
        if not relative_file_path or relative_file_path.strip() == "":
            raise SourceExtractionError("filePath is required.")

        normalized = relative_file_path.replace("\\", "/")
        pure_path = PurePosixPath(normalized)
        if pure_path.is_absolute():
            raise SourceExtractionError("Absolute file paths are not allowed.")
        if ".." in pure_path.parts:
            raise SourceExtractionError("Path traversal is not allowed.")

        candidate = (root / Path(*pure_path.parts)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exception:
            raise SourceExtractionError("File path escapes the repository root.") from exception

        return candidate

    def _validate_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            raise SourceExtractionError("Source file was not found.")
        if file_path.stat().st_size > self.thresholds.max_file_bytes:
            raise SourceExtractionError("Source file is too large to extract safely.")
        if _looks_binary(file_path):
            raise SourceExtractionError("Binary files cannot be extracted as source.")

    def _read_lines(self, file_path: Path) -> list[str]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exception:
            raise SourceExtractionError("Source file could not be read.") from exception

        return content.splitlines()

    def _limit_chars(self, value: str) -> tuple[str, bool]:
        if len(value) <= self.thresholds.max_source_chars:
            return value, False

        return value[:self.thresholds.max_source_chars], True


def _looks_binary(file_path: Path) -> bool:
    try:
        sample = file_path.read_bytes()[:2048]
    except OSError as exception:
        raise SourceExtractionError("Source file could not be inspected.") from exception

    return b"\x00" in sample
