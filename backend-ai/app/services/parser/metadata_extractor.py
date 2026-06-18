import ast
import json
import re
from pathlib import Path
from typing import Any

IMPORT_FROM_PATTERN = re.compile(r"""import\s+[^;]*?\s+from\s+["']([^"']+)["']""")
SIDE_EFFECT_IMPORT_PATTERN = re.compile(r"""import\s+["']([^"']+)["']""")
REQUIRE_PATTERN = re.compile(r"""require\(\s*["']([^"']+)["']\s*\)""")
JAVA_IMPORT_PATTERN = re.compile(r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;", re.MULTILINE)
JS_CLASS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)")
JAVA_TYPE_PATTERN = re.compile(r"\b(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)")
JS_FUNCTION_PATTERN = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(")
JS_ARROW_FUNCTION_PATTERN = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>")
JAVA_FUNCTION_PATTERN = re.compile(
    r"\b(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
    r"(?:[\w<>\[\],.?]+\s+)+([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*(?:throws\s+[\w.,\s]+)?\{"
)


def extract_metadata(file_path: Path, language: str) -> dict[str, Any]:
    content = _read_text(file_path)
    line_count = _line_count(content)

    imports: list[str] = []
    classes: list[str] = []
    functions: list[str] = []

    if language == "python":
        imports, classes, functions = _extract_python_symbols(content)
    elif language == "java":
        imports = _unique(JAVA_IMPORT_PATTERN.findall(content))
        classes = _unique(JAVA_TYPE_PATTERN.findall(content))
        functions = _unique(_java_functions(content, classes))
    elif language in {"javascript", "typescript", "javascriptreact", "typescriptreact"}:
        imports = _extract_javascript_imports(content)
        classes = _unique(JS_CLASS_PATTERN.findall(content))
        functions = _unique(JS_FUNCTION_PATTERN.findall(content) + JS_ARROW_FUNCTION_PATTERN.findall(content))
    elif language == "json":
        _validate_json(content)

    return {
        "lineCount": line_count,
        "sizeBytes": file_path.stat().st_size,
        "imports": imports,
        "classes": classes,
        "functions": functions,
    }


def _read_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="replace")


def _line_count(content: str) -> int:
    if content == "":
        return 0

    return len(content.splitlines())


def _extract_python_symbols(content: str) -> tuple[list[str], list[str], list[str]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [], [], []

    imports: list[str] = []
    classes: list[str] = []
    functions: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    return _unique(imports), _unique(classes), _unique(functions)


def _extract_javascript_imports(content: str) -> list[str]:
    imports = []
    imports.extend(IMPORT_FROM_PATTERN.findall(content))
    imports.extend(SIDE_EFFECT_IMPORT_PATTERN.findall(content))
    imports.extend(REQUIRE_PATTERN.findall(content))
    return _unique(imports)


def _java_functions(content: str, classes: list[str]) -> list[str]:
    class_names = set(classes)
    functions = []

    for function_name in JAVA_FUNCTION_PATTERN.findall(content):
        if function_name not in class_names and function_name not in {"if", "for", "while", "switch", "catch"}:
            functions.append(function_name)

    return functions


def _validate_json(content: str) -> None:
    if content.strip() == "":
        return

    try:
        json.loads(content)
    except json.JSONDecodeError:
        return


def _unique(values: list[str]) -> list[str]:
    seen = set()
    normalized = []

    for value in values:
        if value not in seen:
            seen.add(value)
            normalized.append(value)

    return normalized
