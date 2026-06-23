from pathlib import Path
from uuid import UUID

from app.services.rag.chunk_schema import CodeChunk
from app.services.rag.chunker import chunk_repository
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.qdrant_service import QdrantService


def index_repository_chunks(repository_path: Path, repository_id: UUID, scan_id: UUID) -> dict:
    chunk_result = chunk_repository(repository_path, repository_id, scan_id)
    chunks = [
        CodeChunk(
            repositoryId=repository_id,
            scanId=scan_id,
            filePath=item["filePath"],
            language=item["language"],
            chunkType=item["chunkType"],
            symbolName=item["symbolName"],
            startLine=item["startLine"],
            endLine=item["endLine"],
            content=item["content"],
        )
        for item in chunk_result["chunks"]
    ]

    embeddings = EmbeddingService().embed_texts([chunk.content for chunk in chunks])
    QdrantService().upsert_chunks(chunks, embeddings)

    return {
        "totalChunks": len(chunks),
        "collection": "codepulse_chunks",
    }


def semantic_search(repository_id: UUID | str, query: str, limit: int = 10) -> dict:
    vector = EmbeddingService().embed_text(query)
    results = QdrantService().search(str(repository_id), vector, limit)

    return {
        "repositoryId": str(repository_id),
        "query": query,
        "results": [
            {
                "score": result.get("score"),
                **(result.get("payload") or {}),
            }
            for result in results
        ],
    }
