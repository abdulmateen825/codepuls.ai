from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascriptreact",
    ".tsx": "typescriptreact",
    ".json": "json",
    ".md": "markdown",
    ".yml": "yaml",
    ".yaml": "yaml",
}


def detect_language(file_path: Path) -> str | None:
    return SUPPORTED_EXTENSIONS.get(file_path.suffix.lower())


def is_supported_file(file_path: Path) -> bool:
    return detect_language(file_path) is not None
