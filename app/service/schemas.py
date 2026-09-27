from __future__ import annotations

"""HTTP 层请求 / 响应模型。"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models import ErrorAnalysis, GradingResult


class ImageInput(BaseModel):
    url: Optional[str] = Field(None, description="图片可访问 URL")
    base64: Optional[str] = Field(None, description="图片 base64（可含 data URI 前缀）")

    def to_data_url(self) -> str:
        if self.url:
            return self.url
        b64 = self.base64 or ""
        if b64.startswith("data:"):
            return b64
        return f"data:image/png;base64,{b64}"


class GradeRequest(BaseModel):
    images: List[ImageInput] = Field(default_factory=list, description="学生作业图片")
    student_id: str = Field("anonymous", description="学生标识")
    reference: str = Field("", description="可选：参考答案 / 评分标准")


class AnalyticsRequest(BaseModel):
    student_id: Optional[str] = Field(None, description="留空=全班")
    subject: Optional[str] = Field(None, description="留空=全部学科")


class AgentResponse(BaseModel):
    task: str
    student_id: str = "anonymous"
    grading: Optional[GradingResult] = None
    error_analysis: Optional[ErrorAnalysis] = None
    saved_errors: int = 0
    report: Optional[Dict] = None
    steps: List[str] = Field(default_factory=list)
    error: str = ""
