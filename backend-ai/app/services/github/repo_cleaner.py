import shutil
from pathlib import Path

from app.core.config import get_settings
from app.services.github.file_discovery import IGNORED_DIRECTORIES


def remove_ignored_paths(repository_path: Path) -> None:
    root = repository_path.resolve()

    for child in list(root.rglob("*")):
        if child.name not in IGNORED_DIRECTORIES:
            continue

        if not _is_safe_child(root, child):
            continue

        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        elif child.exists():
            child.unlink(missing_ok=True)


def cleanup_repository(repository_path: Path) -> None:
    root = repository_path.resolve()
    codepulse_root = get_settings().workspace_root.resolve()

    try:
        root.relative_to(codepulse_root)
    except ValueError as exception:
        raise ValueError("Refusing to clean a repository outside the configured workspace root.") from exception

    shutil.rmtree(root, ignore_errors=True)


def _is_safe_child(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False

    return True
