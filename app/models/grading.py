from __future__ import annotations

"""AI 批改相关的结构化模型。

GradingResult 直接作为多模态大模型 with_structured_output 的目标 schema，
保证批改输出可被下游错题分析、学情统计稳定消费。
"""

from typing import List

from pydantic import BaseModel, Field


class QuestionGrade(BaseModel):
    """单题批改结果。"""

    question_no: str = Field(..., description="题号，如 1、2.3、完形16")
    question_type: str = Field("", description="题型：选择/填空/解答/作文等")
    student_answer: str = Field("", description="识别到的学生作答内容")
    correct_answer: str = Field("", description="标准答案或参考答案")
    is_correct: bool = Field(..., description="是否答对")
    score: float = Field(0, description="本题得分")
    max_score: float = Field(0, description="本题满分")
    knowledge_point: str = Field("", description="考查的知识点，如 牛顿第二定律")
    feedback: str = Field("", description="针对本题的简要批注/订正提示")


class GradingResult(BaseModel):
    """一次作业/试卷的完整批改结果。"""

    subject: str = Field("", description="学科，如 数学、物理、英语")
    student_name: str = Field("", description="识别到的学生姓名，未知则留空")
    total_score: float = Field(0, description="试卷总分")
    earned_score: float = Field(0, description="学生实际得分")
    questions: List[QuestionGrade] = Field(
        default_factory=list, description="逐题批改明细"
    )
    overall_comment: str = Field("", description="整体评语")
