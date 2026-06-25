from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SmellType(str, Enum):
    LONG_METHOD = "LONG_METHOD"
    LARGE_CLASS = "LARGE_CLASS"
    HIGH_CYCLOMATIC_COMPLEXITY = "HIGH_CYCLOMATIC_COMPLEXITY"
    DEEP_NESTING = "DEEP_NESTING"
    LONG_PARAMETER_LIST = "LONG_PARAMETER_LIST"
    DUPLICATED_CODE = "DUPLICATED_CODE"
    DEAD_CODE = "DEAD_CODE"
    GOD_OBJECT = "GOD_OBJECT"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SourceContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_snippet: str = Field(default="", alias="codeSnippet", max_length=4000)
    context_before: str = Field(default="", alias="contextBefore", max_length=4000)
    context_after: str = Field(default="", alias="contextAfter", max_length=4000)
    actual_start_line: int = Field(default=1, alias="actualStartLine", ge=1)
    actual_end_line: int = Field(default=1, alias="actualEndLine", ge=1)
    truncated: bool = False

    @model_validator(mode="after")
    def validate_lines(self) -> "SourceContext":
        if self.actual_end_line < self.actual_start_line:
            raise ValueError("actualEndLine must be greater than or equal to actualStartLine.")
        return self


class CodeSmellFinding(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: str = Field(default="CODE_SMELL")
    rule_id: SmellType = Field(alias="ruleId")
    smell_type: SmellType = Field(alias="smellType")
    title: str = Field(min_length=1, max_length=300)
    message: str = Field(min_length=1, max_length=2000)
    severity: Severity
    language: str = Field(min_length=1, max_length=40)
    file_path: str = Field(alias="filePath", min_length=1, max_length=1000)
    start_line: int = Field(alias="startLine", ge=1)
    end_line: int = Field(alias="endLine", ge=1)
    evidence: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    code_snippet: str = Field(default="", alias="codeSnippet", max_length=4000)
    context_before: str = Field(default="", alias="contextBefore", max_length=4000)
    context_after: str = Field(default="", alias="contextAfter", max_length=4000)
    suggested_refactoring: str = Field(default="", alias="suggestedRefactoring", max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value != "CODE_SMELL":
            raise ValueError("Code-smell findings must use category CODE_SMELL.")
        return value

    @model_validator(mode="after")
    def validate_lines_and_rule(self) -> "CodeSmellFinding":
        if self.end_line < self.start_line:
            raise ValueError("endLine must be greater than or equal to startLine.")
        if self.rule_id != self.smell_type:
            raise ValueError("ruleId and smellType must match for code-smell findings.")
        return self

    def to_callback_finding(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "category": self.category,
            "ruleId": self.rule_id.value,
            "smellType": self.smell_type.value,
            "title": self.title,
            "description": self.message,
            "recommendation": self.suggested_refactoring,
            "filePath": self.file_path,
            "lineNumber": self.start_line,
            "startLine": self.start_line,
            "endLine": self.end_line,
            "language": self.language,
            "evidence": self.evidence,
            "metrics": self.metrics,
            "codeSnippet": self.code_snippet,
            "contextBefore": self.context_before,
            "contextAfter": self.context_after,
            "suggestedRefactoring": self.suggested_refactoring,
            "confidence": self.confidence,
            "toolName": "code-smell",
        }


class DetectorWarning(BaseModel):
    detector: str
    language: str | None = None
    message: str = Field(min_length=1, max_length=500)


class DetectorResult(BaseModel):
    detector: str
    status: str
    findings: list[CodeSmellFinding] = Field(default_factory=list)
    warnings: list[DetectorWarning] = Field(default_factory=list)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"completed", "skipped", "failed"}:
            raise ValueError("status must be completed, skipped, or failed.")
        return normalized
