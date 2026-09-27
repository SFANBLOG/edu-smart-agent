from __future__ import annotations

"""错题间隔复习调度 Agent（艾宾浩斯遗忘曲线）。

纯确定性逻辑，不依赖大模型，任何时候可用：
- 回写模式：state.review_ids 非空时，把这些错题标记为「已复习」，
  review_count+1 并按 1/2/4/7/15/30 天递进重排下一次到期日；
- 查询模式：始终返回当前已到期/逾期的待复习清单（逾期越久越靠前）。
"""

from app.agents.state import PipelineState
from app.db import get_store


def _to_item(row: dict) -> dict:
    return {
        "error_id": row["id"],
        "knowledge_point": row.get("knowledge_point", ""),
        "question_no": row.get("question_no", ""),
        "error_type": row.get("error_type", ""),
        "student_answer": row.get("student_answer", ""),
        "correct_answer": row.get("correct_answer", ""),
        "cause": row.get("cause", ""),
        "suggestion": row.get("suggestion", ""),
        "review_count": row.get("review_count", 0) or 0,
        "last_review_at": row.get("last_review_at") or "",
        "next_review_at": row.get("next_review_at") or "",
        "overdue_days": int(row.get("overdue_days") or 0),
    }


async def review_node(state: PipelineState) -> dict:
    steps = ["review"]
    store = get_store()
    sid = state.student_id if state.student_id and state.student_id != "anonymous" else None

    reviewed = 0
    if state.review_ids:
        reviewed = store.mark_reviewed(state.review_ids)

    due = store.due_reviews(student_id=sid, limit=50)
    return {
        "reviewed": reviewed,
        "review_queue": [_to_item(r) for r in due],
        "steps": steps,
    }
