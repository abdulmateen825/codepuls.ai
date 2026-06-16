from pathlib import Path

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    "venv",
    ".venv",
    "__pycache__",
    "pycache",
}


def build_file_tree(repository_path: Path) -> dict:
    safe_root = repository_path.resolve()
    return _build_directory_node(safe_root, safe_root)


def _build_directory_node(path: Path, root: Path) -> dict:
    children = []

    for child in sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if child.is_dir() and child.name in IGNORED_DIRECTORIES:
            continue

        if not _is_safe_child(root, child):
            continue

        if child.is_dir():
            children.append(_build_directory_node(child, root))
            continue

        if child.is_file():
            children.append(
                {
                    "name": child.name,
                    "path": _relative_posix_path(child, root),
                    "type": "file",
                    "sizeBytes": child.stat().st_size,
                }
            )

    return {
        "name": path.name,
        "path": "" if path == root else _relative_posix_path(path, root),
        "type": "directory",
        "children": children,
    }


def _is_safe_child(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False

    return True


def _relative_posix_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()
