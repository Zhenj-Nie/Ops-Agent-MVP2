from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from app.config import settings


class OptionalLLMClient:
    """OpenAI-compatible LLM 占位客户端。

    MVP 默认不强依赖 LLM。设置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL 后可以调用
    OpenAI 兼容接口，用于更复杂的 Planner/Reporter。
    """

    def enabled(self) -> bool:
        return bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        if not self.enabled():
            return None
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": temperature,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
