from __future__ import annotations

"""LangGraph 多智能体管线装配。

拓扑（按 task 路由的两条子流程）：

    START ─(route by task)─┬─ "grade"    ─▶ [grading] ─▶ [error] ─▶ [persist] ─▶ END
                           └─ "analytics"─▶ [stats]   ─▶ [report] ───────────▶ END

- 批改链：多模态批改 → 错题归因 → 落库（积累学情数据）
- 学情链：SQL 客观统计 → 大模型洞察报告
使用 MemorySaver 作为 checkpointer，可按 thread_id 记录多次交互。
"""

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents import analytics_agent, error_agent, grading_agent
from app.agents.state import PipelineState


def route_task(state: PipelineState) -> str:
    return "analytics" if state.task == "analytics" else "grade"


@lru_cache
def get_pipeline():
    builder = StateGraph(PipelineState)

    builder.add_node("grading", grading_agent.grading_node)
    builder.add_node("error", error_agent.error_node)
    builder.add_node("persist", error_agent.persist_node)
    builder.add_node("stats", analytics_agent.stats_node)
    builder.add_node("report", analytics_agent.report_node)

    builder.add_conditional_edges(
        START,
        route_task,
        {"grade": "grading", "analytics": "stats"},
    )
    builder.add_edge("grading", "error")
    builder.add_edge("error", "persist")
    builder.add_edge("persist", END)
    builder.add_edge("stats", "report")
    builder.add_edge("report", END)

    return builder.compile(checkpointer=MemorySaver())
