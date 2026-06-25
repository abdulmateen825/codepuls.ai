from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeSmellThresholds:
    max_method_lines: int = 50
    max_class_lines: int = 300
    max_cyclomatic_complexity: int = 10
    max_nesting_depth: int = 4
    max_parameter_count: int = 5
    min_duplicate_lines: int = 8
    god_object_min_methods: int = 20
    god_object_min_fields: int = 15
    max_snippet_lines: int = 120
    context_lines: int = 5
    max_file_bytes: int = 1_000_000
    max_source_chars: int = 20_000


def load_thresholds() -> CodeSmellThresholds:
    return CodeSmellThresholds(
        max_method_lines=_positive_int("CODE_SMELL_MAX_METHOD_LINES", 50),
        max_class_lines=_positive_int("CODE_SMELL_MAX_CLASS_LINES", 300),
        max_cyclomatic_complexity=_positive_int("CODE_SMELL_MAX_COMPLEXITY", 10),
        max_nesting_depth=_positive_int("CODE_SMELL_MAX_NESTING_DEPTH", 4),
        max_parameter_count=_positive_int("CODE_SMELL_MAX_PARAMETER_COUNT", 5),
        min_duplicate_lines=_positive_int("CODE_SMELL_MIN_DUPLICATE_LINES", 8),
        god_object_min_methods=_positive_int("CODE_SMELL_GOD_OBJECT_MIN_METHODS", 20),
        god_object_min_fields=_positive_int("CODE_SMELL_GOD_OBJECT_MIN_FIELDS", 15),
        max_snippet_lines=_positive_int("CODE_SMELL_MAX_SNIPPET_LINES", 120),
        context_lines=_non_negative_int("CODE_SMELL_CONTEXT_LINES", 5),
        max_file_bytes=_positive_int("CODE_SMELL_MAX_FILE_BYTES", 1_000_000),
        max_source_chars=_positive_int("CODE_SMELL_MAX_SOURCE_CHARS", 20_000),
    )


def _positive_int(name: str, default: int) -> int:
    value = _int_env(name, default)
    return value if value > 0 else default


def _non_negative_int(name: str, default: int) -> int:
    value = _int_env(name, default)
    return value if value >= 0 else default


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default
