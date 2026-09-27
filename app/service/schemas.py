from __future__ import annotations

"""HTTP 层请求 / 响应模型。"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models import ErrorAnalysis, GradingResult, PracticePlan, TutorReply


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


class TutorRequest(BaseModel):
    student_id: str = Field("anonymous", description="学生标识")
    question: str = Field("", description="学生本轮提问")
    history: List[Dict[str, str]] = Field(
        default_factory=list, description="先前对话轮次 [{role, content}]"
    )


class RecommendRequest(BaseModel):
    student_id: str = Field("anonymous", description="目标学生")
    subject: Optional[str] = Field(None, description="限定学科，留空=全部")
    top_k: int = Field(3, ge=1, le=10, description="针对前 k 个薄弱知识点推题")


class ReviewRequest(BaseModel):
    student_id: Optional[str] = Field(None, description="留空=查看全部到期")
    review_ids: List[int] = Field(
        default_factory=list, description="非空则先把这些错题标记为已复习再返回新队列"
    )


class AgentResponse(BaseModel):
    task: str
    student_id: str = "anonymous"
    grading: Optional[GradingResult] = None
    error_analysis: Optional[ErrorAnalysis] = None
    saved_errors: int = 0
    report: Optional[Dict] = None
    tutor_reply: Optional[TutorReply] = None
    practice_plan: Optional[PracticePlan] = None
    review_queue: List[Dict] = Field(default_factory=list)
    reviewed: int = 0
    steps: List[str] = Field(default_factory=list)
    error: str = ""
