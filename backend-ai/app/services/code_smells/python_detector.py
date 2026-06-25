from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from app.services.code_smells.base_detector import BaseCodeSmellDetector
from app.services.code_smells.models import CodeSmellFinding, DetectorResult, Severity, SmellType


class PythonCodeSmellDetector(BaseCodeSmellDetector):
    detector_name = "python-code-smells"
    supported_languages = {"python"}

    def detect(self, repository_root: Path, parsed_files: list[dict[str, Any]]) -> DetectorResult:
        findings: list[CodeSmellFinding] = []

        for parsed_file in parsed_files:
            if not self.supports(parsed_file.get("language")):
                continue

            file_path = str(parsed_file.get("path", ""))
            try:
                source = (repository_root / file_path).read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source)
            except (OSError, SyntaxError, ValueError) as exception:
                return self.failed(f"Python detector could not parse {file_path}: {exception}", "python")

            findings.extend(self._function_findings(tree, parsed_file))
            findings.extend(self._class_findings(tree, parsed_file))
            findings.extend(self._dead_code_findings(tree, parsed_file))

        return DetectorResult(detector=self.detector_name, status="completed", findings=findings)

    def _function_findings(self, tree: ast.AST, parsed_file: dict[str, Any]) -> list[CodeSmellFinding]:
        findings: list[CodeSmellFinding] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            line_count = _line_count(node)
            complexity = _cyclomatic_complexity(node)
            nesting_depth = _max_nesting_depth(node)
            parameter_count = _parameter_count(node)

            if line_count > self.thresholds.max_method_lines:
                findings.append(self._finding(
                    SmellType.LONG_METHOD,
                    Severity.MEDIUM,
                    parsed_file,
                    node.lineno,
                    node.end_lineno or node.lineno,
                    f"Function {node.name} is too long",
                    f"The function contains {line_count} lines.",
                    {"lineCount": line_count, "maximumAllowedLines": self.thresholds.max_method_lines},
                    {"lineCount": line_count, "complexity": complexity},
                    "Extract Method",
                    0.95,
                ))

            if complexity > self.thresholds.max_cyclomatic_complexity:
                findings.append(self._finding(
                    SmellType.HIGH_CYCLOMATIC_COMPLEXITY,
                    Severity.HIGH,
                    parsed_file,
                    node.lineno,
                    node.end_lineno or node.lineno,
                    f"Function {node.name} is too complex",
                    f"The function has cyclomatic complexity {complexity}.",
                    {
                        "cyclomaticComplexity": complexity,
                        "maximumAllowedComplexity": self.thresholds.max_cyclomatic_complexity,
                    },
                    {"complexity": complexity, "lineCount": line_count},
                    "Split conditional branches into smaller functions",
                    0.94,
                ))

            if nesting_depth > self.thresholds.max_nesting_depth:
                findings.append(self._finding(
                    SmellType.DEEP_NESTING,
                    Severity.MEDIUM,
                    parsed_file,
                    node.lineno,
                    node.end_lineno or node.lineno,
                    f"Function {node.name} is deeply nested",
                    f"The function reaches nesting depth {nesting_depth}.",
                    {"nestingDepth": nesting_depth, "maximumAllowedDepth": self.thresholds.max_nesting_depth},
                    {"nestingDepth": nesting_depth},
                    "Use guard clauses or extract nested logic",
                    0.9,
                ))

            if parameter_count > self.thresholds.max_parameter_count:
                findings.append(self._finding(
                    SmellType.LONG_PARAMETER_LIST,
                    Severity.MEDIUM,
                    parsed_file,
                    node.lineno,
                    node.lineno,
                    f"Function {node.name} has too many parameters",
                    f"The function declares {parameter_count} parameters.",
                    {
                        "parameterCount": parameter_count,
                        "maximumAllowedParameters": self.thresholds.max_parameter_count,
                    },
                    {"parameterCount": parameter_count},
                    "Introduce Parameter Object",
                    0.96,
                ))

        return findings

    def _class_findings(self, tree: ast.AST, parsed_file: dict[str, Any]) -> list[CodeSmellFinding]:
        findings: list[CodeSmellFinding] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            line_count = _line_count(node)
            methods = [child for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))]
            fields = _class_field_count(node)

            if line_count > self.thresholds.max_class_lines:
                findings.append(self._finding(
                    SmellType.LARGE_CLASS,
                    Severity.MEDIUM,
                    parsed_file,
                    node.lineno,
                    node.end_lineno or node.lineno,
                    f"Class {node.name} is too large",
                    f"The class contains {line_count} lines.",
                    {"lineCount": line_count, "maximumAllowedLines": self.thresholds.max_class_lines},
                    {"lineCount": line_count, "methodCount": len(methods), "fieldCount": fields},
                    "Extract Class",
                    0.91,
                ))

            if len(methods) >= self.thresholds.god_object_min_methods and fields >= self.thresholds.god_object_min_fields:
                findings.append(self._finding(
                    SmellType.GOD_OBJECT,
                    Severity.HIGH,
                    parsed_file,
                    node.lineno,
                    node.end_lineno or node.lineno,
                    f"Class {node.name} concentrates too many responsibilities",
                    f"The class declares {len(methods)} methods and {fields} fields.",
                    {
                        "methodCount": len(methods),
                        "fieldCount": fields,
                        "minimumMethods": self.thresholds.god_object_min_methods,
                        "minimumFields": self.thresholds.god_object_min_fields,
                    },
                    {"methodCount": len(methods), "fieldCount": fields},
                    "Split responsibilities into focused services or value objects",
                    0.82,
                ))

        return findings

    def _dead_code_findings(self, tree: ast.AST, parsed_file: dict[str, Any]) -> list[CodeSmellFinding]:
        findings: list[CodeSmellFinding] = []
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if not isinstance(body, list):
                continue

            terminal_seen = False
            for child in body:
                if terminal_seen and hasattr(child, "lineno"):
                    findings.append(self._finding(
                        SmellType.DEAD_CODE,
                        Severity.LOW,
                        parsed_file,
                        child.lineno,
                        getattr(child, "end_lineno", child.lineno) or child.lineno,
                        "Unreachable code after terminal statement",
                        "This statement appears after return, raise, break, or continue.",
                        {"terminalStatementBeforeLine": child.lineno},
                        {"lineNumber": child.lineno},
                        "Remove unreachable code",
                        0.84,
                    ))
                    break
                terminal_seen = isinstance(child, (ast.Return, ast.Raise, ast.Break, ast.Continue))

        return findings

    def _finding(
        self,
        smell_type: SmellType,
        severity: Severity,
        parsed_file: dict[str, Any],
        start_line: int,
        end_line: int,
        title: str,
        message: str,
        evidence: dict[str, Any],
        metrics: dict[str, Any],
        suggested_refactoring: str,
        confidence: float,
    ) -> CodeSmellFinding:
        return CodeSmellFinding(
            ruleId=smell_type,
            smellType=smell_type,
            severity=severity,
            language=str(parsed_file.get("language", "python")).upper(),
            filePath=str(parsed_file.get("path", "")),
            startLine=start_line,
            endLine=end_line,
            title=title,
            message=message,
            evidence=evidence,
            metrics=metrics,
            suggestedRefactoring=suggested_refactoring,
            confidence=confidence,
        )


def _line_count(node: ast.AST) -> int:
    return max(1, (getattr(node, "end_lineno", None) or getattr(node, "lineno", 1)) - getattr(node, "lineno", 1) + 1)


def _parameter_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    args = node.args
    return len(args.posonlyargs) + len(args.args) + len(args.kwonlyargs) + int(args.vararg is not None) + int(args.kwarg is not None)


def _cyclomatic_complexity(node: ast.AST) -> int:
    complexity = 1
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.ExceptHandler,
        ast.With,
        ast.AsyncWith,
        ast.IfExp,
        ast.Match,
    )
    for child in ast.walk(node):
        if isinstance(child, branch_nodes):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(1, len(child.values) - 1)
    return complexity


def _max_nesting_depth(node: ast.AST) -> int:
    nesting_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)

    def visit(current: ast.AST, depth: int) -> int:
        next_depth = depth + 1 if isinstance(current, nesting_nodes) else depth
        child_depths = [visit(child, next_depth) for child in ast.iter_child_nodes(current)]
        return max([next_depth, *child_depths])

    return visit(node, 0)


def _class_field_count(node: ast.ClassDef) -> int:
    fields = 0
    for child in node.body:
        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            fields += 1
        if isinstance(child, ast.FunctionDef) and child.name == "__init__":
            for init_child in ast.walk(child):
                if isinstance(init_child, (ast.Assign, ast.AnnAssign)):
                    targets = getattr(init_child, "targets", [getattr(init_child, "target", None)])
                    for target in targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                            fields += 1
    return fields
