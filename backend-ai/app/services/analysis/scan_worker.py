from app.schemas.internal_analysis import AnalyzeRequest
from app.services.github.file_discovery import build_file_tree
from app.services.github.repo_cleaner import remove_ignored_paths
from app.services.github.repo_cloner import clone_public_repository
from app.services.parser.file_parser import parse_repository


def prepare_repository_for_scan(request: AnalyzeRequest) -> dict:
    repository_path = clone_public_repository(
        scan_id=request.scan_id,
        github_url=request.github_url,
        branch=request.branch,
    )
    remove_ignored_paths(repository_path)
    return {
        "fileTree": build_file_tree(repository_path),
        "parsedFiles": parse_repository(repository_path),
    }


def process_scan_placeholder(request: AnalyzeRequest, repository_metadata: dict) -> None:
    _ = request
    _ = repository_metadata
    # Placeholder for static analysis and callback persistence.
