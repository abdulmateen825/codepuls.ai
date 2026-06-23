from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scan_id: UUID = Field(alias="scanId")
    repository_id: UUID = Field(alias="repositoryId")
    github_url: str = Field(alias="githubUrl", min_length=1, max_length=500)
    branch: str = Field(default="main", min_length=1, max_length=120)


class AnalyzeAcceptedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    accepted: bool
    scan_id: UUID = Field(alias="scanId")
    status: str
    file_tree: dict = Field(alias="fileTree")
    parsed_files: dict = Field(alias="parsedFiles")
    analysis: dict
