import hashlib
import json
import os
from typing import Any
from urllib import error, request
from uuid import NAMESPACE_URL, uuid5

from app.services.rag.chunk_schema import CodeChunk

COLLECTION_NAME = "codepulse_chunks"
DEFAULT_VECTOR_SIZE = 384


class QdrantServiceError(RuntimeError):
    pass


class QdrantService:
    def __init__(self) -> None:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = os.getenv("QDRANT_PORT", "6333")
        self.base_url = os.getenv("QDRANT_URL", f"http://{host}:{port}").rstrip("/")
        self.collection_name = os.getenv("QDRANT_COLLECTION", COLLECTION_NAME)
        self.vector_size = int(os.getenv("EMBEDDING_VECTOR_SIZE", str(DEFAULT_VECTOR_SIZE)))

    def ensure_collection(self, vector_size: int | None = None) -> None:
        size = vector_size or self.vector_size
        payload = {
            "vectors": {
                "size": size,
                "distance": "Cosine",
            }
        }
        self._request("PUT", f"/collections/{self.collection_name}", payload)

    def upsert_chunks(self, chunks: list[CodeChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors must have the same length.")

        if not chunks:
            return

        self.ensure_collection(len(vectors[0]))
        points = [
            {
                "id": _point_id(chunk),
                "vector": vector,
                "payload": chunk.to_dict(),
            }
            for chunk, vector in zip(chunks, vectors)
        ]

        self._request(
            "PUT",
            f"/collections/{self.collection_name}/points?wait=true",
            {"points": points},
        )

    def search(self, repository_id: str, vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        payload = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "filter": {
                "must": [
                    {
                        "key": "repositoryId",
                        "match": {
                            "value": repository_id,
                        },
                    }
                ]
            },
        }

        data = self._request("POST", f"/collections/{self.collection_name}/points/search", payload)
        return data.get("result", [])

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        qdrant_request = request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )

        try:
            with request.urlopen(qdrant_request, timeout=20) as response:
                content = response.read().decode("utf-8")
        except error.HTTPError as exception:
            details = exception.read().decode("utf-8", errors="replace")
            raise QdrantServiceError(f"Qdrant request failed with status {exception.code}: {details}") from exception
        except OSError as exception:
            raise QdrantServiceError("Qdrant request failed.") from exception

        if not content:
            return {}

        return json.loads(content)


def _point_id(chunk: CodeChunk) -> str:
    raw_id = "|".join(
        [
            str(chunk.repositoryId),
            str(chunk.scanId),
            chunk.filePath,
            chunk.chunkType,
            chunk.symbolName or "",
            str(chunk.startLine),
            str(chunk.endLine),
        ]
    )
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
    return str(uuid5(NAMESPACE_URL, digest))
