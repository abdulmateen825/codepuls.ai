from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1, max_length=4000)


class RepositoryChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    repository_id: UUID = Field(alias="repositoryId")
    question: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class FileReference(BaseModel):
    file_path: str = Field(alias="filePath")
    start_line: int = Field(alias="startLine")
    end_line: int = Field(alias="endLine")
    symbol_name: str | None = Field(default=None, alias="symbolName")
    score: float | None = None


class RepositoryChatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str
    file_references: list[FileReference] = Field(alias="fileReferences")
    suggested_questions: list[str] = Field(alias="suggestedQuestions")


class FindingExplainRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    repository_id: UUID = Field(alias="repositoryId")
    scan_id: UUID = Field(alias="scanId")
    finding_id: UUID = Field(alias="findingId")
    severity: str
    category: str
    title: str
    description: str
    recommendation: str | None = None
    file_path: str = Field(alias="filePath")
    line_number: int | None = Field(default=None, alias="lineNumber")
    rule_id: str = Field(alias="ruleId")


class FindingExplanationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: str
    why_it_matters: str = Field(alias="whyItMatters")
    risk: str
    corrective_action: str = Field(alias="correctiveAction")
    possible_fixed_code: str = Field(alias="possibleFixedCode")
    confidence_score: float = Field(alias="confidenceScore", ge=0, le=1)
    file_references: list[FileReference] = Field(default_factory=list, alias="fileReferences")
