from __future__ import annotations

"""LangGraph 多智能体管线装配。

拓扑（按 task 路由的多条子流程）：

    START ─(route by task)─┬─ "grade"    ─▶ [grading] ─▶ [error] ─▶ [persist] ─▶ END
                           ├─ "analytics"─▶ [stats]   ─▶ [report] ───────────▶ END
                           ├─ "tutor"    ─▶ [tutor]                          ─▶ END
                           ├─ "recommend"─▶ [recommend]                      ─▶ END
                           └─ "review"   ─▶ [review]                         ─▶ END

- 批改链：多模态批改 → 错题归因 → 落库（积累学情数据）
- 学情链：SQL 客观统计 → 大模型洞察报告
- 辅导链：结合错题落点的苏格拉底式多轮启发
- 推题链：薄弱点定位 → 变式练习生成
- 复习链：基于遗忘曲线的错题到期调度与回写
使用 MemorySaver 作为 checkpointer，可按 thread_id 记录多次交互。
"""

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents import (
    analytics_agent,
    error_agent,
    grading_agent,
    recommend_agent,
    review_agent,
    tutor_agent,
)
from app.agents.state import PipelineState

_ROUTE = {
    "grade": "grading",
    "analytics": "stats",
    "tutor": "tutor",
    "recommend": "recommend",
    "review": "review",
}


def route_task(state: PipelineState) -> str:
    return state.task if state.task in _ROUTE else "grade"


@lru_cache
def get_pipeline():
    builder = StateGraph(PipelineState)

    builder.add_node("grading", grading_agent.grading_node)
    builder.add_node("error", error_agent.error_node)
    builder.add_node("persist", error_agent.persist_node)
    builder.add_node("stats", analytics_agent.stats_node)
    builder.add_node("report", analytics_agent.report_node)
    builder.add_node("tutor", tutor_agent.tutor_node)
    builder.add_node("recommend", recommend_agent.recommend_node)
    builder.add_node("review", review_agent.review_node)

    builder.add_conditional_edges(START, route_task, _ROUTE)
    builder.add_edge("grading", "error")
    builder.add_edge("error", "persist")
    builder.add_edge("persist", END)
    builder.add_edge("stats", "report")
    builder.add_edge("report", END)
    builder.add_edge("tutor", END)
    builder.add_edge("recommend", END)
    builder.add_edge("review", END)

    return builder.compile(checkpointer=MemorySaver())
