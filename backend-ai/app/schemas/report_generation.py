from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportFinding(BaseModel):
    severity: str
    category: str
    title: str
    description: str
    recommendation: str | None = None
    file_path: str = Field(alias="filePath")
    line_number: int | None = Field(default=None, alias="lineNumber")
    rule_id: str = Field(alias="ruleId")


class GenerateReportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scan_id: UUID = Field(alias="scanId")
    repository_id: UUID = Field(alias="repositoryId")
    repository_full_name: str = Field(alias="repositoryFullName")
    repository_url: str = Field(alias="repositoryUrl")
    status: str
    quality_score: int | None = Field(default=None, alias="qualityScore")
    security_score: int | None = Field(default=None, alias="securityScore")
    maintainability_score: int | None = Field(default=None, alias="maintainabilityScore")
    findings: list[ReportFinding] = Field(default_factory=list)
