"""Small OpenAI-compatible JSON client for graph extraction."""

import json

from openai import OpenAI

from src.config import get_settings


class LLMClientError(RuntimeError):
    """Raised when the configured LLM cannot return valid JSON."""


class GraphLLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.settings.llm_api_key:
            raise LLMClientError("LLM_API_KEY is not configured")
        if not self.settings.llm_model:
            raise LLMClientError("LLM_MODEL is not configured")

        client = OpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            timeout=8.0,
        )
        response = client.chat.completions.create(
            model=self.settings.llm_model,
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
