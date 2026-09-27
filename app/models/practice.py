from __future__ import annotations

"""智能推题 / 复习调度 / 辅导对话相关模型。

- PracticeItem / PracticePlan：个性化推题 Agent 的输出（弱项变式题）
- ReviewItem：间隔复习调度产出的待复习条目
- TutorReply：苏格拉底式辅导 Agent 的单轮回复
"""

from typing import List

from pydantic import BaseModel, Field


class PracticeItem(BaseModel):
    """单道推荐练习题。"""

    knowledge_point: str = Field("", description="针对的薄弱知识点")
    stem: str = Field(..., description="题干（自行改编，不抄原题）")
    answer: str = Field("", description="参考答案")
    difficulty: str = Field("基础", description="难度：基础/提高/挑战")
    hint: str = Field("", description="解题思路提示（不直接给答案）")
    why: str = Field("", description="为什么推荐这道题（关联哪条错题）")


class PracticePlan(BaseModel):
    """一次个性化推题的完整输出。"""

    student_id: str = Field("", description="目标学生")
    items: List[PracticeItem] = Field(default_factory=list, description="推荐题目列表")
    plan_summary: str = Field("", description="练习计划说明（题量/顺序/建议用时）")


class ReviewItem(BaseModel):
    """待复习错题条目（含记忆状态）。"""

    error_id: int = Field(..., description="错题本记录 id")
    knowledge_point: str = ""
    question_no: str = ""
    error_type: str = ""
    student_answer: str = ""
    correct_answer: str = ""
    cause: str = ""
    suggestion: str = ""
    review_count: int = Field(0, description="已复习次数")
    last_review_at: str = Field("", description="上次复习时间")
    next_review_at: str = Field("", description="下次应复习时间（艾宾浩斯间隔）")
    overdue_days: int = Field(0, description="距到期已逾期天数")


class TutorReply(BaseModel):
    """辅导 Agent 的单轮回复。"""

    reply: str = Field("", description="Agent 的回复内容（引导式，不直接报答案）")
    grounded_points: List[str] = Field(
        default_factory=list, description="本轮引用的该生薄弱知识点"
    )
