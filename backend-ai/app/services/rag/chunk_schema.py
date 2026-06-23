from dataclasses import asdict, dataclass
from uuid import UUID


@dataclass(frozen=True)
class CodeChunk:
    repositoryId: UUID
    scanId: UUID
    filePath: str
    language: str
    chunkType: str
    symbolName: str | None
    startLine: int
    endLine: int
    content: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["repositoryId"] = str(self.repositoryId)
        data["scanId"] = str(self.scanId)
        return data
