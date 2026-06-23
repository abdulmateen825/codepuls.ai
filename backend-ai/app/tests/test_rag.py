import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from app.services.rag.chunker import chunk_file, chunk_repository
from app.services.rag.chunk_schema import CodeChunk
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.qdrant_service import QdrantService
from app.services.rag.retriever import index_repository_chunks, semantic_search


class RagTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_id = UUID("22222222-2222-2222-2222-222222222222")
        self.scan_id = UUID("11111111-1111-1111-1111-111111111111")

    def test_chunk_python_file_prefers_function_and_class_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "service.py"
            file_path.write_text(
                "class Worker:\n"
                "    def run(self):\n"
                "        return True\n\n"
                "def helper():\n"
                "    return False\n",
                encoding="utf-8",
            )

            chunks = chunk_file(file_path, root, self.repository_id, self.scan_id)

        chunk_names = {(chunk.chunkType, chunk.symbolName) for chunk in chunks}
        self.assertIn(("class", "Worker"), chunk_names)
        self.assertIn(("function", "run"), chunk_names)
        self.assertIn(("function", "helper"), chunk_names)
        self.assertEqual(chunks[0].repositoryId, self.repository_id)
        self.assertEqual(chunks[0].scanId, self.scan_id)
        self.assertEqual(chunks[0].filePath, "service.py")
        self.assertEqual(chunks[0].language, "python")

    def test_chunk_repository_uses_file_chunks_for_non_symbol_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.json").write_text('{"enabled": true}\n', encoding="utf-8")

            result = chunk_repository(root, self.repository_id, self.scan_id)

        self.assertEqual(result["totalChunks"], 1)
        self.assertEqual(result["chunks"][0]["chunkType"], "file")
        self.assertEqual(result["chunks"][0]["filePath"], "config.json")

    def test_embedding_service_returns_normalized_deterministic_vectors(self) -> None:
        service = EmbeddingService()
        service.provider = "local"
        service.vector_size = 16

        first = service.embed_text("def run scan")
        second = service.embed_text("def run scan")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertAlmostEqual(sum(value * value for value in first), 1.0)

    def test_qdrant_upsert_creates_collection_and_points(self) -> None:
        chunk = CodeChunk(
            repositoryId=self.repository_id,
            scanId=self.scan_id,
            filePath="service.py",
            language="python",
            chunkType="function",
            symbolName="run",
            startLine=1,
            endLine=3,
            content="def run():\n    pass",
        )

        with patch.object(QdrantService, "_request", return_value={}) as qdrant_request:
            QdrantService().upsert_chunks([chunk], [[0.1, 0.2, 0.3]])

        self.assertEqual(qdrant_request.call_args_list[0].args[0], "PUT")
        self.assertIn("/collections/codepulse_chunks", qdrant_request.call_args_list[0].args[1])
        points_payload = qdrant_request.call_args_list[1].args[2]
        self.assertEqual(points_payload["points"][0]["payload"]["filePath"], "service.py")
        self.assertEqual(points_payload["points"][0]["payload"]["repositoryId"], str(self.repository_id))

    def test_semantic_search_filters_by_repository_id(self) -> None:
        with patch.object(EmbeddingService, "embed_text", return_value=[0.1, 0.2]), \
                patch.object(QdrantService, "search", return_value=[{"score": 0.9, "payload": {"filePath": "service.py"}}]) as search:
            result = semantic_search(self.repository_id, "scan service")

        search.assert_called_once_with(str(self.repository_id), [0.1, 0.2], 10)
        self.assertEqual(result["results"][0]["score"], 0.9)
        self.assertEqual(result["results"][0]["filePath"], "service.py")

    def test_index_repository_chunks_embeds_and_upserts_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text("def main():\n    pass\n", encoding="utf-8")

            with patch.object(EmbeddingService, "embed_texts", return_value=[[0.1, 0.2]]) as embed, \
                    patch.object(QdrantService, "upsert_chunks") as upsert:
                result = index_repository_chunks(root, self.repository_id, self.scan_id)

        self.assertEqual(result["totalChunks"], 1)
        embed.assert_called_once()
        upsert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
