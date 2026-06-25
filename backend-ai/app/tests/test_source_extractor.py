import os
import tempfile
import unittest
from pathlib import Path

from app.services.code_smells.config import CodeSmellThresholds
from app.services.code_smells.source_extractor import SourceExtractionError, SourceExtractor


class SourceExtractorTest(unittest.TestCase):
    def test_extracts_code_with_context_and_preserves_formatting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text("one\n  two\n    three\nfour\n", encoding="utf-8")

            context = SourceExtractor(CodeSmellThresholds(context_lines=1)).extract(root, "app.py", 2, 3)

        self.assertEqual(context.context_before, "one")
        self.assertEqual(context.code_snippet, "  two\n    three")
        self.assertEqual(context.context_after, "four")
        self.assertEqual(context.actual_start_line, 2)
        self.assertEqual(context.actual_end_line, 3)

    def test_rejects_absolute_and_traversal_paths(self) -> None:
        extractor = SourceExtractor(CodeSmellThresholds())

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with self.assertRaises(SourceExtractionError):
                extractor.extract(root, str(root / "app.py"), 1, 1)

            with self.assertRaises(SourceExtractionError):
                extractor.extract(root, "../app.py", 1, 1)

    def test_rejects_symlink_that_escapes_repository(self) -> None:
        if os.name == "nt":
            self.skipTest("Symlink creation may require Windows developer mode or admin privileges.")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside.py"
            root.mkdir()
            outside.write_text("print('outside')\n", encoding="utf-8")
            (root / "link.py").symlink_to(outside)

            with self.assertRaises(SourceExtractionError):
                SourceExtractor(CodeSmellThresholds()).extract(root, "link.py", 1, 1)

    def test_rejects_binary_and_oversized_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "binary.py").write_bytes(b"abc\x00def")
            (root / "large.py").write_text("x" * 20, encoding="utf-8")
            extractor = SourceExtractor(CodeSmellThresholds(max_file_bytes=10))

            with self.assertRaises(SourceExtractionError):
                extractor.extract(root, "binary.py", 1, 1)

            with self.assertRaises(SourceExtractionError):
                extractor.extract(root, "large.py", 1, 1)

    def test_handles_unicode_mixed_line_endings_and_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "unicode.py").write_bytes("α\r\nβ\nγ\rδ\r\n".encode("utf-8"))

            context = SourceExtractor(CodeSmellThresholds(max_snippet_lines=2, context_lines=0)).extract(
                root,
                "unicode.py",
                1,
                4,
            )

        self.assertEqual(context.code_snippet, "α\nβ")
        self.assertTrue(context.truncated)
        self.assertEqual(context.actual_start_line, 1)
        self.assertEqual(context.actual_end_line, 2)

    def test_rejects_invalid_line_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            extractor = SourceExtractor(CodeSmellThresholds())

            with self.assertRaises(SourceExtractionError):
                extractor.extract(root, "app.py", 0, 1)

            with self.assertRaises(SourceExtractionError):
                extractor.extract(root, "app.py", 2, 1)


if __name__ == "__main__":
    unittest.main()
