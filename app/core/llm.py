from __future__ import annotations

"""模型工厂。

- get_vlm(): 多模态视觉模型，用于「AI 批改」读取学生作业图片。
- get_llm(): 文本推理模型，用于「错题归因」「学情报告」。

统一走 OpenAI 兼容协议：换国内多模态大模型（qwen-vl / GLM-4V 等）
只需改 .env 的 OPENAI_BASE_URL 与模型名，业务代码零改动。
"""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import get_settings


@lru_cache
def get_vlm(temperature: float = 0.0) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.vlm_model,
        temperature=temperature,
        api_key=s.openai_api_key or "EMPTY",
        base_url=s.openai_base_url,
    )


@lru_cache
def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.llm_model,
        temperature=temperature,
        api_key=s.openai_api_key or "EMPTY",
        base_url=s.openai_base_url,
        streaming=True,
    )
