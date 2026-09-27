from __future__ import annotations

"""集中式配置，使用 pydantic-settings 从 .env / 环境变量读取。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- 模型（OpenAI 兼容） ----
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    vlm_model: str = "gpt-4o-mini"  # 多模态视觉：AI 批改
    llm_model: str = "gpt-4o-mini"  # 文本推理：错题归因 / 学情报告

    # ---- 服务 ----
    host: str = "0.0.0.0"
    port: int = 8000
    app_name: str = "Edu Smart Agent"

    # ---- 数据 ----
    db_path: str = "data/edu.db"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
