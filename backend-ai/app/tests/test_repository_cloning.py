import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from app.services.github.file_discovery import build_file_tree
from app.services.github.repo_cleaner import cleanup_repository, remove_ignored_paths
from app.services.github.repo_cloner import (
    RepositoryCloneError,
    normalize_branch,
    normalize_github_url,
    scan_workspace,
)


class RepositoryCloningTest(unittest.TestCase):
    def test_normalize_github_url_accepts_public_https_repository(self) -> None:
        self.assertEqual(
            normalize_github_url("https://github.com/codepulse/backend-core"),
            "https://github.com/codepulse/backend-core.git",
        )

    def test_normalize_github_url_rejects_unsafe_hosts_and_paths(self) -> None:
        with self.assertRaises(RepositoryCloneError):
            normalize_github_url("https://example.com/codepulse/backend-core")

        with self.assertRaises(RepositoryCloneError):
            normalize_github_url("https://github.com/codepulse/../backend-core")

    def test_normalize_branch_rejects_unsafe_segments(self) -> None:
        self.assertEqual(normalize_branch("feature/scans"), "feature/scans")

        with self.assertRaises(RepositoryCloneError):
            normalize_branch("../main")

    def test_scan_workspace_is_scoped_to_tmp_codepulse(self) -> None:
        scan_id = uuid4()
        workspace = scan_workspace(scan_id)

        self.assertEqual(workspace.name, str(scan_id))
        self.assertEqual(workspace.parent, Path("/tmp/codepulse").resolve())

    def test_remove_ignored_paths_and_build_file_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir) / "repo"
            (repository / ".git").mkdir(parents=True)
            (repository / "node_modules").mkdir()
            (repository / "__pycache__").mkdir()
            (repository / "src").mkdir()
            (repository / ".git" / "config").write_text("private", encoding="utf-8")
            (repository / "node_modules" / "leftpad.js").write_text("", encoding="utf-8")
            (repository / "__pycache__" / "module.pyc").write_text("", encoding="utf-8")
            (repository / "src" / "main.py").write_text("print('ok')", encoding="utf-8")

            remove_ignored_paths(repository)
            tree = build_file_tree(repository)

            self.assertFalse((repository / ".git").exists())
            self.assertFalse((repository / "node_modules").exists())
            self.assertFalse((repository / "__pycache__").exists())
            self.assertEqual(tree["children"][0]["name"], "src")
            self.assertEqual(tree["children"][0]["children"][0]["path"], "src/main.py")

    def test_cleanup_repository_rejects_paths_outside_codepulse_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                cleanup_repository(Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
