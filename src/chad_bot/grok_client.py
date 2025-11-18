from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class ChatResult:
    content: str
    usage: Dict[str, Any]
    raw: Dict[str, Any]


class GrokClient:
    def __init__(self, *, api_key: Optional[str], api_base: str, chat_model: str):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.chat_model = chat_model
        # Persistent HTTP client with connection pooling
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the persistent async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                timeout=30.0,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        *,
        system_prompt: str,
        user_content: str,
        temperature: float,
        max_tokens: int,
    ) -> ChatResult:
        if not self.api_key:
            fake = {
                "choices": [{"message": {"content": "[stubbed response because GROK_API_KEY is missing]"}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            return ChatResult(content=fake["choices"][0]["message"]["content"], usage=fake["usage"], raw=fake)

        payload = {
            "model": self.chat_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        client = await self._get_client()
        resp = await client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return ChatResult(content=choice, usage=usage, raw=data)
