import json
import os
from urllib import request


class LlmServiceError(RuntimeError):
    pass


class LlmService:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "fallback").strip().lower()
        self.model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "openai":
            return self._complete_with_openai(system_prompt, user_prompt)

        return self._fallback_completion(user_prompt)

    def _complete_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LlmServiceError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        openai_request = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(openai_request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except OSError as exception:
            raise LlmServiceError("OpenAI chat completion failed.") from exception

        return data["choices"][0]["message"]["content"]

    def _fallback_completion(self, user_prompt: str) -> str:
        return (
            "I reviewed the available repository context and generated a deterministic response because no LLM provider "
            "is configured.\n\n"
            f"{user_prompt[:1200]}"
        )
