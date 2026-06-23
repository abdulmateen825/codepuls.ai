import ast
import re
from pathlib import Path
from uuid import UUID

from app.services.github.file_discovery import IGNORED_DIRECTORIES
from app.services.parser.language_detector import detect_language, is_supported_file
from app.services.rag.chunk_schema import CodeChunk

JS_CLASS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)")
JS_FUNCTION_PATTERN = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(")
JS_ARROW_FUNCTION_PATTERN = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
)
JAVA_TYPE_PATTERN = re.compile(r"\b(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)")
JAVA_FUNCTION_PATTERN = re.compile(
    r"\b(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
    r"(?:[\w<>\[\],.?]+\s+)+([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*(?:throws\s+[\w.,\s]+)?\{"
)
MAX_FILE_CHUNK_LINES = 120


def chunk_repository(repository_path: Path, repository_id: UUID, scan_id: UUID) -> dict:
    root = repository_path.resolve()
    chunks = []

    for file_path in _iter_supported_files(root):
        chunks.extend(chunk_file(file_path, root, repository_id, scan_id))

    return {
        "totalChunks": len(chunks),
        "chunks": [chunk.to_dict() for chunk in chunks],
    }


def chunk_file(file_path: Path, repository_root: Path, repository_id: UUID, scan_id: UUID) -> list[CodeChunk]:
    root = repository_root.resolve()
    safe_file_path = file_path.resolve()

    try:
        relative_path = safe_file_path.relative_to(root).as_posix()
    except ValueError as exception:
        raise ValueError("Refusing to chunk a file outside the repository root.") from exception

    language = detect_language(safe_file_path)
    if language is None:
        return []

    content = safe_file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    if not lines:
        return []

    symbol_ranges = _symbol_ranges(content, language)
    chunks = [
        _chunk_from_range(
            repository_id=repository_id,
            scan_id=scan_id,
            file_path=relative_path,
            language=language,
            chunk_type=chunk_type,
            symbol_name=symbol_name,
            start_line=start_line,
            end_line=end_line,
            lines=lines,
        )
        for chunk_type, symbol_name, start_line, end_line in symbol_ranges
    ]

    if chunks:
        return chunks

    return _file_chunks(repository_id, scan_id, relative_path, language, lines)


def _symbol_ranges(content: str, language: str) -> list[tuple[str, str, int, int]]:
    if language == "python":
        return _python_symbol_ranges(content)

    if language == "java":
        return _brace_symbol_ranges(content, JAVA_TYPE_PATTERN, JAVA_FUNCTION_PATTERN)

    if language in {"javascript", "typescript", "javascriptreact", "typescriptreact"}:
        return _brace_symbol_ranges(
            content,
            JS_CLASS_PATTERN,
            _combined_js_function_pattern(),
        )

    return []


def _python_symbol_ranges(content: str) -> list[tuple[str, str, int, int]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    ranges = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            ranges.append(("class", node.name, node.lineno, _end_line(node)))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ranges.append(("function", node.name, node.lineno, _end_line(node)))

    return sorted(_dedupe_ranges(ranges), key=lambda item: (item[2], item[3], item[1]))


def _brace_symbol_ranges(
    content: str,
    class_pattern: re.Pattern,
    function_pattern: re.Pattern,
) -> list[tuple[str, str, int, int]]:
    ranges = []

    for match in class_pattern.finditer(content):
        start_line = _line_number_at(content, match.start())
        end_line = _brace_end_line(content, match.end())
        if end_line:
            ranges.append(("class", match.group(1), start_line, end_line))

    for match in function_pattern.finditer(content):
        start_line = _line_number_at(content, match.start())
        end_line = _brace_end_line(content, match.end())
        if end_line:
            ranges.append(("function", _match_symbol_name(match), start_line, end_line))

    return sorted(_dedupe_ranges(ranges), key=lambda item: (item[2], item[3], item[1]))


def _combined_js_function_pattern() -> re.Pattern:
    return re.compile(f"{JS_FUNCTION_PATTERN.pattern}|{JS_ARROW_FUNCTION_PATTERN.pattern}")


def _match_symbol_name(match: re.Match) -> str:
    for group in match.groups():
        if group:
            return group
    return "anonymous"


def _brace_end_line(content: str, search_from: int) -> int | None:
    open_index = content.find("{", search_from)
    if open_index == -1:
        return None

    depth = 0
    for index in range(open_index, len(content)):
        character = content[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return _line_number_at(content, index)

    return _line_number_at(content, len(content))


def _line_number_at(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def _end_line(node: ast.AST) -> int:
    return max(getattr(node, "end_lineno", None) or getattr(node, "lineno", 1), getattr(node, "lineno", 1))


def _chunk_from_range(
    repository_id: UUID,
    scan_id: UUID,
    file_path: str,
    language: str,
    chunk_type: str,
    symbol_name: str | None,
    start_line: int,
    end_line: int,
    lines: list[str],
) -> CodeChunk:
    safe_start = max(1, start_line)
    safe_end = min(len(lines), max(safe_start, end_line))
    return CodeChunk(
        repositoryId=repository_id,
        scanId=scan_id,
        filePath=file_path,
        language=language,
        chunkType=chunk_type,
        symbolName=symbol_name,
        startLine=safe_start,
        endLine=safe_end,
        content="\n".join(lines[safe_start - 1:safe_end]),
    )


def _file_chunks(
    repository_id: UUID,
    scan_id: UUID,
    file_path: str,
    language: str,
    lines: list[str],
) -> list[CodeChunk]:
    chunks = []
    for index in range(0, len(lines), MAX_FILE_CHUNK_LINES):
        start_line = index + 1
        end_line = min(len(lines), index + MAX_FILE_CHUNK_LINES)
        suffix = "" if len(lines) <= MAX_FILE_CHUNK_LINES else f":{start_line}-{end_line}"
        chunks.append(
            _chunk_from_range(
                repository_id=repository_id,
                scan_id=scan_id,
                file_path=file_path,
                language=language,
                chunk_type="file",
                symbol_name=Path(file_path).name + suffix,
                start_line=start_line,
                end_line=end_line,
                lines=lines,
            )
        )
    return chunks


def _dedupe_ranges(ranges: list[tuple[str, str, int, int]]) -> list[tuple[str, str, int, int]]:
    seen = set()
    deduped = []

    for item in ranges:
        key = (item[0], item[1], item[2], item[3])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def _iter_supported_files(root: Path):
    for file_path in sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix()):
        if not file_path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in file_path.relative_to(root).parts):
            continue

        if is_supported_file(file_path):
            yield file_path
