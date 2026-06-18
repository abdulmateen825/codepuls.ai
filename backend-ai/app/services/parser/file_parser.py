from pathlib import Path
from typing import Any

from app.services.github.file_discovery import IGNORED_DIRECTORIES
from app.services.parser.language_detector import detect_language, is_supported_file
from app.services.parser.metadata_extractor import extract_metadata


def parse_repository(repository_path: Path) -> dict[str, Any]:
    root = repository_path.resolve()
    files = []

    for file_path in _iter_supported_files(root):
        files.append(parse_file(file_path, root))

    return {
        "totalFiles": len(files),
        "files": files,
    }


def parse_file(file_path: Path, repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    safe_file_path = file_path.resolve()

    try:
        relative_path = safe_file_path.relative_to(root)
    except ValueError as exception:
        raise ValueError("Refusing to parse a file outside the repository root.") from exception

    language = detect_language(safe_file_path)
    if language is None:
        raise ValueError("Unsupported file type.")

    metadata = extract_metadata(safe_file_path, language)

    return {
        "path": relative_path.as_posix(),
        "language": language,
        **metadata,
    }


def _iter_supported_files(root: Path):
    for file_path in sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix()):
        if not file_path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in file_path.relative_to(root).parts):
            continue

        if is_supported_file(file_path):
            yield file_path
