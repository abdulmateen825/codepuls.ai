import hashlib
import json
import math
import os
from urllib import request

DEFAULT_VECTOR_SIZE = 384


class EmbeddingServiceError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.vector_size = int(os.getenv("EMBEDDING_VECTOR_SIZE", str(DEFAULT_VECTOR_SIZE)))
        self._sentence_model = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self.provider == "openai":
            return self._embed_with_openai(texts)

        sentence_embeddings = self._embed_with_sentence_transformers(texts)
        if sentence_embeddings is not None:
            return sentence_embeddings

        return [self._deterministic_embedding(text) for text in texts]

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _embed_with_sentence_transformers(self, texts: list[str]) -> list[list[float]] | None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None

        if self._sentence_model is None:
            self._sentence_model = SentenceTransformer(self.model_name)

        vectors = self._sentence_model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]

    def _embed_with_openai(self, texts: list[str]) -> list[list[float]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EmbeddingServiceError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")

        payload = json.dumps(
            {
                "model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                "input": texts,
            }
        ).encode("utf-8")
        openai_request = request.Request(
            "https://api.openai.com/v1/embeddings",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(openai_request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except OSError as exception:
            raise EmbeddingServiceError("OpenAI embedding request failed.") from exception

        return [item["embedding"] for item in data["data"]]

    def _deterministic_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.vector_size
        tokens = [token for token in _tokenize(text) if token]

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.vector_size
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector

        return [value / magnitude for value in vector]


def _tokenize(text: str) -> list[str]:
    normalized = []
    token = []

    for character in text.lower():
        if character.isalnum() or character in {"_", "-"}:
            token.append(character)
            continue

        if token:
            normalized.append("".join(token))
            token = []

    if token:
        normalized.append("".join(token))

    return normalized
