from __future__ import annotations

"""学情分析相关模型。

LearningReport 汇聚来自 SQLite 的客观统计（纯 SQL 计算，无需大模型），
再可选地由文本大模型补充自然语言洞察与教学建议（narrative 字段）。
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class KnowledgeMastery(BaseModel):
    """单个知识点的掌握度。"""

    knowledge_point: str
    attempts: int = Field(0, description="该知识点被作答/考查次数")
    wrong: int = Field(0, description="其中错误次数")
    mastery_rate: float = Field(0, description="掌握率 = 1 - 错误/考查")


class LearningReport(BaseModel):
    """学情分析报告。"""

    scope: str = Field("", description="统计范围，如 全班 / 某学生 / 某学科")
    total_gradings: int = Field(0, description="批改记录数")
    total_errors: int = Field(0, description="错题记录数")
    avg_score_rate: float = Field(0, description="平均得分率 0-1")
    knowledge_mastery: List[KnowledgeMastery] = Field(
        default_factory=list, description="各知识点掌握度"
    )
    error_type_dist: Dict[str, int] = Field(
        default_factory=dict, description="错误类型分布"
    )
    weak_points: List[str] = Field(
        default_factory=list, description="掌握率最低的薄弱知识点 Top-N"
    )
    narrative: str = Field("", description="大模型生成的学情洞察与教学建议")
