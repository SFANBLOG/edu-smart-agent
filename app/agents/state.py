from __future__ import annotations

"""多智能体流水线的共享状态。

task 字段驱动图入口路由：
- "grade"    : 批改 → 错题分析 → 入库（图片输入，多模态）
- "analytics": 读取统计 → 学情洞察
其余字段在各节点间累积传递。
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models import ErrorAnalysis, GradingResult


class PipelineState(BaseModel):
    # 路由用任务类型
    task: str = "grade"

    # ---- 批改任务输入 ----
    student_id: str = "anonymous"
    images: List[str] = Field(default_factory=list)  # data URL 或 http URL
    reference: str = ""  # 可选：参考答案 / 评分标准

    # ---- 中间 / 输出产物 ----
    grading: Optional[GradingResult] = None
    error_analysis: Optional[ErrorAnalysis] = None
    saved_errors: int = 0

    # ---- 学情任务输入 / 输出 ----
    subject: Optional[str] = None
    report: Optional[dict] = None

    # ---- 流程日志（可观测 / 流式展示） ----
    steps: List[str] = Field(default_factory=list)
    error: str = ""
