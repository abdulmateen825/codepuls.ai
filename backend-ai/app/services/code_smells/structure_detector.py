from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.code_smells.base_detector import BaseCodeSmellDetector
from app.services.code_smells.models import CodeSmellFinding, DetectorResult, Severity, SmellType

FUNCTION_PATTERN = re.compile(
    r"(?P<prefix>\b(?:public|private|protected|static|final|async|export|function|const|let|var|\w+[<>\w,\s\[\]?]*\s+)+)"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"(?:=\s*(?:async\s*)?)?\((?P<params>[^)]*)\)\s*(?:=>\s*)?\{"
)
CLASS_PATTERN = re.compile(r"\b(?:class|interface|enum|record)\s+(?P<name>[A-Za-z_$][\w$]*)")
FIELD_PATTERN = re.compile(r"^\s*(?:private|protected|public)?\s*(?:static\s+)?(?:readonly\s+)?[A-Za-z_$][\w$<>\[\]?]*\s+[A-Za-z_$][\w$]*\s*(?:=|;)", re.MULTILINE)


@dataclass(frozen=True)
class Block:
    name: str
    start_line: int
    end_line: int
    content: str
    params: str = ""


class StructureCodeSmellDetector(BaseCodeSmellDetector):
    detector_name = "structure-code-smells"
    supported_languages = {"java", "javascript", "typescript", "javascriptreact", "typescriptreact"}

    def detect(self, repository_root: Path, parsed_files: list[dict[str, Any]]) -> DetectorResult:
        findings: list[CodeSmellFinding] = []

        for parsed_file in parsed_files:
            if not self.supports(parsed_file.get("language")):
                continue

            file_path = str(parsed_file.get("path", ""))
            try:
                source = (repository_root / file_path).read_text(encoding="utf-8", errors="replace")
            except OSError as exception:
                return self.failed(f"Structure detector could not read {file_path}: {exception}", parsed_file.get("language"))

            functions = _find_blocks(source, FUNCTION_PATTERN)
            classes = _find_blocks(source, CLASS_PATTERN)

            for function in functions:
                findings.extend(self._function_findings(function, parsed_file))

            for class_block in classes:
                findings.extend(self._class_findings(class_block, parsed_file, functions))

        return DetectorResult(detector=self.detector_name, status="completed", findings=findings)

    def _function_findings(self, function: Block, parsed_file: dict[str, Any]) -> list[CodeSmellFinding]:
        findings: list[CodeSmellFinding] = []
        line_count = _line_count(function)
        complexity = _complexity(function.content)
        nesting_depth = _nesting_depth(function.content)
        parameter_count = _parameter_count(function.params)

        if line_count > self.thresholds.max_method_lines:
            findings.append(self._finding(
                SmellType.LONG_METHOD,
                Severity.MEDIUM,
                parsed_file,
                function.start_line,
                function.end_line,
                f"Function {function.name} is too long",
                f"The function contains {line_count} lines.",
                {"lineCount": line_count, "maximumAllowedLines": self.thresholds.max_method_lines},
                {"lineCount": line_count, "complexity": complexity},
                "Extract Method",
                0.82,
            ))

        if complexity > self.thresholds.max_cyclomatic_complexity:
            findings.append(self._finding(
                SmellType.HIGH_CYCLOMATIC_COMPLEXITY,
                Severity.HIGH,
                parsed_file,
                function.start_line,
                function.end_line,
                f"Function {function.name} is too complex",
                f"The function has estimated cyclomatic complexity {complexity}.",
                {"cyclomaticComplexity": complexity, "maximumAllowedComplexity": self.thresholds.max_cyclomatic_complexity},
                {"complexity": complexity, "lineCount": line_count},
                "Split conditional branches into smaller functions",
                0.8,
            ))

        if nesting_depth > self.thresholds.max_nesting_depth:
            findings.append(self._finding(
                SmellType.DEEP_NESTING,
                Severity.MEDIUM,
                parsed_file,
                function.start_line,
                function.end_line,
                f"Function {function.name} is deeply nested",
                f"The function reaches estimated nesting depth {nesting_depth}.",
                {"nestingDepth": nesting_depth, "maximumAllowedDepth": self.thresholds.max_nesting_depth},
                {"nestingDepth": nesting_depth},
                "Use guard clauses or extract nested logic",
                0.78,
            ))

        if parameter_count > self.thresholds.max_parameter_count:
            findings.append(self._finding(
                SmellType.LONG_PARAMETER_LIST,
                Severity.MEDIUM,
                parsed_file,
                function.start_line,
                function.start_line,
                f"Function {function.name} has too many parameters",
                f"The function declares {parameter_count} parameters.",
                {"parameterCount": parameter_count, "maximumAllowedParameters": self.thresholds.max_parameter_count},
                {"parameterCount": parameter_count},
                "Introduce Parameter Object",
                0.86,
            ))

        return findings

    def _class_findings(self, class_block: Block, parsed_file: dict[str, Any], functions: list[Block]) -> list[CodeSmellFinding]:
        findings: list[CodeSmellFinding] = []
        line_count = _line_count(class_block)
        method_count = sum(
            1
            for function in functions
            if function.start_line >= class_block.start_line and function.end_line <= class_block.end_line
        )
        field_count = len(FIELD_PATTERN.findall(class_block.content))

        if line_count > self.thresholds.max_class_lines:
            findings.append(self._finding(
                SmellType.LARGE_CLASS,
                Severity.MEDIUM,
                parsed_file,
                class_block.start_line,
                class_block.end_line,
                f"Class {class_block.name} is too large",
                f"The class contains {line_count} lines.",
                {"lineCount": line_count, "maximumAllowedLines": self.thresholds.max_class_lines},
                {"lineCount": line_count, "methodCount": method_count, "fieldCount": field_count},
                "Extract Class",
                0.78,
            ))

        if method_count >= self.thresholds.god_object_min_methods and field_count >= self.thresholds.god_object_min_fields:
            findings.append(self._finding(
                SmellType.GOD_OBJECT,
                Severity.HIGH,
                parsed_file,
                class_block.start_line,
                class_block.end_line,
                f"Class {class_block.name} concentrates too many responsibilities",
                f"The class declares {method_count} methods and {field_count} fields.",
                {
                    "methodCount": method_count,
                    "fieldCount": field_count,
                    "minimumMethods": self.thresholds.god_object_min_methods,
                    "minimumFields": self.thresholds.god_object_min_fields,
                },
                {"methodCount": method_count, "fieldCount": field_count},
                "Split responsibilities into focused services or value objects",
                0.74,
            ))

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
            language=str(parsed_file.get("language", "")).upper(),
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


def _find_blocks(source: str, pattern: re.Pattern) -> list[Block]:
    blocks: list[Block] = []
    line_starts = _line_starts(source)

    for match in pattern.finditer(source):
        open_brace = source.find("{", match.end() - 1)
        if open_brace < 0:
            continue

        close_brace = _matching_brace(source, open_brace)
        if close_brace is None:
            continue

        blocks.append(Block(
            name=match.group("name"),
            start_line=_line_number(line_starts, match.start()),
            end_line=_line_number(line_starts, close_brace),
            content=source[match.start():close_brace + 1],
            params=match.groupdict().get("params", ""),
        ))

    return blocks


def _matching_brace(source: str, open_brace: int) -> int | None:
    depth = 0
    for index in range(open_brace, len(source)):
        character = source[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _line_starts(source: str) -> list[int]:
    starts = [0]
    starts.extend(index + 1 for index, character in enumerate(source) if character == "\n")
    return starts


def _line_number(line_starts: list[int], offset: int) -> int:
    line = 1
    for index, start in enumerate(line_starts, start=1):
        if start > offset:
            break
        line = index
    return line


def _line_count(block: Block) -> int:
    return max(1, block.end_line - block.start_line + 1)


def _parameter_count(params: str) -> int:
    cleaned = params.strip()
    if not cleaned:
        return 0
    return len([param for param in cleaned.split(",") if param.strip()])


def _complexity(content: str) -> int:
    tokens = re.findall(r"\b(if|for|while|case|catch|&&|\|\||\?)\b", content)
    return 1 + len(tokens)


def _nesting_depth(content: str) -> int:
    depth = 0
    maximum = 0
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^(if|for|while|switch|try|catch)\b", stripped):
            maximum = max(maximum, depth + 1)
        depth += line.count("{")
        depth -= line.count("}")
        depth = max(0, depth)
    return maximum
