import tempfile
import unittest
from pathlib import Path

from app.services.parser.file_parser import parse_file, parse_repository
from app.services.parser.language_detector import detect_language, is_supported_file


class FileParserTest(unittest.TestCase):
    def test_detect_language_for_supported_files(self) -> None:
        self.assertEqual(detect_language(Path("app.py")), "python")
        self.assertEqual(detect_language(Path("App.java")), "java")
        self.assertEqual(detect_language(Path("index.tsx")), "typescriptreact")
        self.assertEqual(detect_language(Path("workflow.yml")), "yaml")
        self.assertTrue(is_supported_file(Path("README.md")))
        self.assertFalse(is_supported_file(Path("image.png")))

    def test_parse_python_file_extracts_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "service.py"
            file_path.write_text(
                "import os\nfrom app.core import settings\n\nclass Worker:\n    async def run(self):\n        pass\n\ndef helper():\n    pass\n",
                encoding="utf-8",
            )

            metadata = parse_file(file_path, root)

        self.assertEqual(metadata["path"], "service.py")
        self.assertEqual(metadata["language"], "python")
        self.assertEqual(metadata["lineCount"], 9)
        self.assertEqual(metadata["imports"], ["os", "app.core"])
        self.assertEqual(metadata["classes"], ["Worker"])
        self.assertEqual(metadata["functions"], ["helper", "run"])
        self.assertGreater(metadata["sizeBytes"], 0)

    def test_parse_java_file_extracts_imports_classes_and_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "RepositoryService.java"
            file_path.write_text(
                "import java.util.List;\npublic class RepositoryService {\n public List<String> getAll() { return List.of(); }\n}\n",
                encoding="utf-8",
            )

            metadata = parse_file(file_path, root)

        self.assertEqual(metadata["imports"], ["java.util.List"])
        self.assertEqual(metadata["classes"], ["RepositoryService"])
        self.assertEqual(metadata["functions"], ["getAll"])

    def test_parse_typescript_file_extracts_imports_classes_and_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "dashboard.ts"
            file_path.write_text(
                "import { api } from './api';\nconst load = async () => api.get();\nfunction render() {}\nclass Dashboard {}\n",
                encoding="utf-8",
            )

            metadata = parse_file(file_path, root)

        self.assertEqual(metadata["imports"], ["./api"])
        self.assertEqual(metadata["classes"], ["Dashboard"])
        self.assertEqual(metadata["functions"], ["render", "load"])

    def test_parse_repository_returns_normalized_json_and_ignores_unsupported_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "node_modules").mkdir()
            (root / "src" / "app.py").write_text("def main():\n    pass\n", encoding="utf-8")
            (root / "src" / "config.json").write_text('{"ok": true}\n', encoding="utf-8")
            (root / "node_modules" / "ignored.js").write_text("function ignored() {}\n", encoding="utf-8")
            (root / "logo.svg").write_text("<svg />\n", encoding="utf-8")

            parsed = parse_repository(root)

        self.assertEqual(parsed["totalFiles"], 2)
        self.assertEqual([file["path"] for file in parsed["files"]], ["src/app.py", "src/config.json"])
        self.assertEqual(parsed["files"][0]["language"], "python")
        self.assertEqual(parsed["files"][1]["language"], "json")

    def test_parse_file_rejects_paths_outside_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as other_dir:
            root = Path(root_dir)
            file_path = Path(other_dir) / "outside.py"
            file_path.write_text("print('unsafe')\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                parse_file(file_path, root)


if __name__ == "__main__":
    unittest.main()
