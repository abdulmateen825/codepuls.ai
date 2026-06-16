import shutil
import subprocess
from pathlib import Path
from uuid import UUID
from urllib.parse import urlparse

CODEPULSE_TMP_ROOT = Path("/tmp/codepulse")
MAX_BRANCH_LENGTH = 120


class RepositoryCloneError(RuntimeError):
    pass


def clone_public_repository(scan_id: UUID, github_url: str, branch: str = "main") -> Path:
    workspace = scan_workspace(scan_id)
    safe_github_url = normalize_github_url(github_url)
    safe_branch = normalize_branch(branch)

    if workspace.exists():
        shutil.rmtree(workspace)

    workspace.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--branch",
        safe_branch,
        safe_github_url,
        str(workspace),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.CalledProcessError as exception:
        raise RepositoryCloneError(_clone_error_message(exception.stderr)) from exception
    except subprocess.TimeoutExpired as exception:
        raise RepositoryCloneError("Repository clone timed out.") from exception

    return workspace


def scan_workspace(scan_id: UUID) -> Path:
    root = CODEPULSE_TMP_ROOT.resolve()
    workspace = (root / str(scan_id)).resolve()

    if root != workspace.parent:
        raise RepositoryCloneError("Unsafe scan workspace path.")

    return workspace


def normalize_github_url(github_url: str) -> str:
    parsed = urlparse(github_url.strip())

    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise RepositoryCloneError("Only public HTTPS GitHub repository URLs are supported.")

    segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
    if len(segments) != 2:
        raise RepositoryCloneError("GitHub URL must point to a repository.")

    owner, name = segments
    name = name.removesuffix(".git")

    if not _is_safe_github_segment(owner) or not _is_safe_github_segment(name):
        raise RepositoryCloneError("GitHub URL contains unsafe path segments.")

    return f"https://github.com/{owner}/{name}.git"


def normalize_branch(branch: str | None) -> str:
    value = (branch or "main").strip()

    if not value or len(value) > MAX_BRANCH_LENGTH:
        raise RepositoryCloneError("Branch name is invalid.")

    if value.startswith(("/", "-")) or ".." in value or value.endswith(("/", ".")):
        raise RepositoryCloneError("Branch name contains unsafe path segments.")

    if not all(character.isalnum() or character in "._/-" for character in value):
        raise RepositoryCloneError("Branch name contains unsupported characters.")

    return value


def _is_safe_github_segment(value: str) -> bool:
    return (
        0 < len(value) <= 120
        and value not in {".", ".."}
        and all(character.isalnum() or character in "._-" for character in value)
    )


def _clone_error_message(stderr: str) -> str:
    if "Remote branch" in stderr and "not found" in stderr:
        return "Requested branch was not found."

    if "Repository not found" in stderr:
        return "Repository was not found or is not public."

    return "Repository clone failed."
