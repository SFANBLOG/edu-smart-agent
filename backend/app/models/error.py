from __future__ import annotations

"""错题分析相关模型。

- ErrorItem / ErrorAnalysis：错题分析 Agent 的输出（逐题归因）。
- ErrorRecord：持久化到 SQLite 错题本的记录行。
"""

from typing import List

from pydantic import BaseModel, Field

# 统一错误类型枚举（便于学情统计聚合）
ERROR_TYPES = ["概念不清", "计算失误", "审题偏差", "方法不会", "表达/规范", "其他"]


class ErrorItem(BaseModel):
    """单道错题的归因分析结果。"""

    question_no: str = Field(..., description="题号")
    knowledge_point: str = Field("", description="涉及知识点")
    error_type: str = Field("其他", description=f"错误类型，取值范围：{ERROR_TYPES}")
    cause: str = Field("", description="错因分析（为什么错）")
    suggestion: str = Field("", description="针对性订正与练习建议")


class ErrorAnalysis(BaseModel):
    """一次批改的错题分析汇总输出。"""

    errors: List[ErrorItem] = Field(default_factory=list, description="错题归因明细")
    summary: str = Field("", description="本次错题的整体诊断小结")


class ErrorRecord(BaseModel):
    """错题本持久化记录（含上下文）。"""

    student_id: str
    subject: str
    question_no: str
    knowledge_point: str
    error_type: str
    student_answer: str = ""
    correct_answer: str = ""
    cause: str = ""
    suggestion: str = ""
    created_at: str = ""
