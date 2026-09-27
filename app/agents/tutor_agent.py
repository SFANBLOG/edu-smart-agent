from __future__ import annotations

"""苏格拉底式辅导 Agent（多轮对话）。

给定学生本轮提问，结合其错题本沉淀的薄弱知识点做「有据启发」：
不直接报答案，而是抛出一个循序渐进的引导问题。会话历史由前端回传
（history），配合 LangGraph checkpointer 的 thread_id 维持上下文。

未配置密钥时退化为基于薄弱知识点的模板启发，保证对话链路可用。
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.prompts import TUTOR_SYSTEM
from app.agents.state import PipelineState
from app.config import get_settings
from app.core.llm import get_llm
from app.db import get_store
from app.models import TutorReply


def _grounded_context(student_id: str) -> tuple[str, list[str]]:
    """拉取该生掌握率最低的知识点，作为辅导的落点。"""
    sid = student_id if student_id and student_id != "anonymous" else None
    mastery = get_store().knowledge_mastery(student_id=sid, top=5)
    weak = [m["knowledge_point"] for m in mastery if m["mastery_rate"] < 1.0][:5]
    if not weak:
        return "", []
    lines = [
        f"- {m['knowledge_point']}（掌握率 {int(m['mastery_rate'] * 100)}%）"
        for m in mastery
        if m["knowledge_point"] in weak
    ]
    return "该学生近期薄弱知识点：\n" + "\n".join(lines), weak


async def tutor_node(state: PipelineState) -> dict:
    steps = ["tutor"]
    ctx, weak = _grounded_context(state.student_id)

    if not state.question.strip():
        return {
            "tutor_reply": TutorReply(reply="请把不懂的题目或你的思路告诉我，我们一起拆解。"),
            "steps": steps,
        }

    if not get_settings().llm_enabled:
        hint = f"我们先从「{weak[0]}」这个点入手。" if weak else ""
        fallback = (
            f"{hint}先别急着要答案——这道题里，你能确定条件的哪一步？"
            "把你的想法说出来，我再顺着你的思路给下一个提示。"
            "（未配置密钥，当前为模板启发）"
        )
        return {
            "tutor_reply": TutorReply(reply=fallback, grounded_points=weak),
            "steps": steps,
        }

    messages: list = [SystemMessage(content=TUTOR_SYSTEM)]
    if ctx:
        messages.append(SystemMessage(content=ctx))
    for turn in state.history[-8:]:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
    messages.append(HumanMessage(content=state.question))

    try:
        resp = await get_llm().ainvoke(messages)
        reply = resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as e:  # 辅导失败不影响主流程
        reply = f"（辅导暂时不可用：{e}）"
    return {"tutor_reply": TutorReply(reply=reply, grounded_points=weak), "steps": steps}
