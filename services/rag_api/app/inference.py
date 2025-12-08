import os
from functools import lru_cache
from typing import Optional

import httpx

DEFAULT_INFERENCE_URL = "http://localhost:8000/generate"


class InferenceClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0) -> None:
        self.base_url = base_url or os.getenv("INFERENCE_URL", DEFAULT_INFERENCE_URL)
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
        }
        resp = self._client.post(self.base_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", "")


@lru_cache(maxsize=1)
def get_inference_client() -> InferenceClient:
    return InferenceClient()
