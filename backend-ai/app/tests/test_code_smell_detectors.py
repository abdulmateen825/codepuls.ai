import tempfile
import unittest
from pathlib import Path

from app.services.code_smells.config import CodeSmellThresholds
from app.services.code_smells.runner import run_code_smell_detection


class CodeSmellDetectorsTest(unittest.TestCase):
    def test_python_detector_reports_all_core_smells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = "\n".join([
                "class God:",
                *[f"    field_{index} = {index}" for index in range(4)],
                "    def too_many(self, a, b, c):",
                "        if a:",
                "            if b:",
                "                if c:",
                "                    return 1",
                "        return 0",
                "        print('dead')",
                "    def helper(self):",
                "        return 1",
                "    def another(self):",
                "        return 2",
            ])
            (root / "app.py").write_text(source, encoding="utf-8")
            parsed = {
                "files": [
                    {
                        "path": "app.py",
                        "language": "python",
                        "lineCount": len(source.splitlines()),
                        "classes": ["God"],
                        "functions": ["too_many", "helper", "another"],
                    }
                ]
            }

            result = run_code_smell_detection(
                root,
                parsed,
                CodeSmellThresholds(
                    max_method_lines=4,
                    max_class_lines=8,
                    max_cyclomatic_complexity=2,
                    max_nesting_depth=2,
                    max_parameter_count=2,
                    god_object_min_methods=3,
                    god_object_min_fields=4,
                ),
            )

        smell_types = {finding["smellType"] for finding in result["findings"]}

        self.assertIn("LONG_METHOD", smell_types)
        self.assertIn("LARGE_CLASS", smell_types)
        self.assertIn("HIGH_CYCLOMATIC_COMPLEXITY", smell_types)
        self.assertIn("DEEP_NESTING", smell_types)
        self.assertIn("LONG_PARAMETER_LIST", smell_types)
        self.assertIn("DEAD_CODE", smell_types)
        self.assertIn("GOD_OBJECT", smell_types)

    def test_structure_detector_reports_java_smells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = """
class OrderService {
  private String a;
  private String b;
  public void process(String a, String b, String c) {
    if (a != null) {
      if (b != null) {
        if (c != null) {
          System.out.println(c);
        }
      }
    }
  }
}
""".strip()
            path = root / "OrderService.java"
            path.write_text(source, encoding="utf-8")
            parsed = {"files": [{"path": "OrderService.java", "language": "java"}]}

            result = run_code_smell_detection(
                root,
                parsed,
                CodeSmellThresholds(
                    max_method_lines=4,
                    max_class_lines=6,
                    max_cyclomatic_complexity=2,
                    max_nesting_depth=2,
                    max_parameter_count=2,
                    god_object_min_methods=10,
                    god_object_min_fields=10,
                ),
            )

        smell_types = {finding["smellType"] for finding in result["findings"]}

        self.assertIn("LONG_METHOD", smell_types)
        self.assertIn("LARGE_CLASS", smell_types)
        self.assertIn("LONG_PARAMETER_LIST", smell_types)

    def test_duplicate_detector_reports_repeated_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            block = [
                "value = input_data.get('value')",
                "if value is None:",
                "    value = 'fallback'",
                "result.append(value.strip())",
            ]
            (root / "a.py").write_text("\n".join(["def a(input_data, result):", *["    " + line for line in block]]), encoding="utf-8")
            (root / "b.py").write_text("\n".join(["def b(input_data, result):", *["    " + line for line in block]]), encoding="utf-8")
            parsed = {
                "files": [
                    {"path": "a.py", "language": "python"},
                    {"path": "b.py", "language": "python"},
                ]
            }

            result = run_code_smell_detection(root, parsed, CodeSmellThresholds(min_duplicate_lines=4))

        self.assertIn("DUPLICATED_CODE", {finding["smellType"] for finding in result["findings"]})

    def test_unsupported_language_creates_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# docs\n", encoding="utf-8")
            result = run_code_smell_detection(root, {"files": [{"path": "README.md", "language": "markdown"}]})

        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
