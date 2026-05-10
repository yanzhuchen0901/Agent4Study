"""Small OpenAI-compatible JSON client for graph extraction."""

import json

from openai import OpenAI

from src.config import get_settings


class LLMClientError(RuntimeError):
    """Raised when the configured LLM cannot return valid JSON."""


class GraphLLMClient:
    def __init__(self, llm_config: dict | None = None) -> None:
        self.settings = get_settings()
        self.llm_config = llm_config or {}

    def _pick(self, key: str, fallback: str) -> str:
        value = self.llm_config.get(key)
        if value is None:
            return fallback
        text = str(value).strip()
        return text or fallback

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        api_key = self._pick("api_key", self.settings.llm_api_key)
        model = self._pick("model", self.settings.llm_model)
        base_url = self._pick("base_url", self.settings.llm_base_url)

        if not api_key:
            raise LLMClientError("LLM_API_KEY is not configured")
        if not model:
            raise LLMClientError("LLM_MODEL is not configured")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=8.0,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMClientError(f"LLM returned invalid JSON: {content[:300]}") from exc
