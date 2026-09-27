from __future__ import annotations

"""个性化智能推题 Agent。

先从错题本沉淀中定位薄弱知识点，取其典型错题作为「变式依据」，
再让大模型为每个薄弱点改编同类题（换情境/换数据/升难度）。

未配置密钥时不臆造题目，改为把典型错题连同订正建议回推为
「重做原题 + 思路提示」的保守练习计划，保证端点始终有可用产出。
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import RECOMMEND_SYSTEM
from app.agents.state import PipelineState
from app.config import get_settings
from app.core.llm import get_llm
from app.db import get_store
from app.models import PracticeItem, PracticePlan


def _weak_with_errors(student_id: str, subject, top_k: int):
    sid = student_id if student_id and student_id != "anonymous" else None
    mastery = get_store().knowledge_mastery(student_id=sid, subject=subject, top=top_k * 2)
    weak = [m["knowledge_point"] for m in sorted(mastery, key=lambda x: x["mastery_rate"])[:top_k]]
    if not weak:
        return [], []
    errs = get_store().errors_by_weak_points(weak, student_id=sid)
    return weak, errs


async def recommend_node(state: PipelineState) -> dict:
    steps = ["recommend"]
    weak, errs = _weak_with_errors(state.student_id, state.subject, state.top_k)

    if not weak:
        return {
            "practice_plan": PracticePlan(
                student_id=state.student_id,
                plan_summary="暂无薄弱知识点数据，请先批改作业或运行 seed_demo 灌入演示数据。",
            ),
            "steps": steps,
        }

    # 无密钥：保守回推典型错题重做计划（不编造新题）
    if not get_settings().llm_enabled:
        items = [
            PracticeItem(
                knowledge_point=e["knowledge_point"],
                stem=f"【重做 · 巩固】{e['question_no']} 题：{e['student_answer'] or '（原题作答见错题本）'}",
                answer=e["correct_answer"],
                difficulty="基础",
                hint=e["suggestion"] or "先盖住答案独立重做，再对照订正。",
                why=f"该知识点「{e['knowledge_point']}」近期错误（{e['error_type']}）。",
            )
            for e in errs
        ]
        plan = PracticePlan(
            student_id=state.student_id,
            items=items,
            plan_summary=f"针对薄弱点 {weak}，先重做典型错题巩固（未配置密钥，暂不生成新变式题）。",
        )
        return {"practice_plan": plan, "steps": steps}

    structured = get_llm().with_structured_output(PracticePlan)
    payload = {
        "weak_points": weak,
        "typical_errors": [
            {
                "knowledge_point": e["knowledge_point"],
                "error_type": e["error_type"],
                "student_answer": e["student_answer"],
                "correct_answer": e["correct_answer"],
                "cause": e["cause"],
            }
            for e in errs
        ],
    }
    user = HumanMessage(
        content="请据此为该生改编变式练习题：\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    plan: PracticePlan = await structured.ainvoke(
        [SystemMessage(content=RECOMMEND_SYSTEM), user]
    )
    plan.student_id = state.student_id
    return {"practice_plan": plan, "steps": steps}
