from __future__ import annotations

"""学情分析 Agent。

- stats_node : 从 SQLite 聚合客观指标（平均得分率、知识点掌握度、错误类型分布、薄弱点）。
              纯 SQL 计算，无需大模型即可产出，保证无 Key 也能出统计。
- report_node: 用文本大模型基于客观统计生成自然语言学情洞察与教学建议。
              无 Key 时跳过叙述，仅返回客观数据。
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import ANALYTICS_SYSTEM
from app.agents.state import PipelineState
from app.config import get_settings
from app.core.llm import get_llm
from app.db import get_store


async def stats_node(state: PipelineState) -> dict:
    steps = ["stats"]
    store = get_store()
    sid = state.student_id if state.student_id and state.student_id != "anonymous" else None
    subject = state.subject

    summary = store.summary_stats(student_id=sid, subject=subject)
    mastery = store.knowledge_mastery(student_id=sid, subject=subject, top=20)
    dist = store.error_type_dist(student_id=sid, subject=subject)

    # 掌握率最低的 5 个知识点作为薄弱点
    weak = [m["knowledge_point"] for m in sorted(mastery, key=lambda x: x["mastery_rate"])[:5]]

    scope = "全班" if not sid else f"学生:{sid}"
    if subject:
        scope += f" · {subject}"

    report = {
        "scope": scope,
        **summary,
        "knowledge_mastery": mastery,
        "error_type_dist": dist,
        "weak_points": weak,
        "narrative": "",
    }
    return {"report": report, "steps": steps}


async def report_node(state: PipelineState) -> dict:
    steps = ["report"]
    report = state.report or {}
    if not get_settings().llm_enabled or report.get("total_gradings", 0) == 0:
        return {"steps": steps}

    metrics = {
        k: report[k]
        for k in ("scope", "total_gradings", "total_errors", "avg_score_rate", "error_type_dist", "weak_points")
    }
    user = HumanMessage(
        content="客观学情统计如下，请生成学情洞察与教学建议：\n"
        + json.dumps(metrics, ensure_ascii=False)
    )
    try:
        resp = await get_llm().ainvoke([SystemMessage(content=ANALYTICS_SYSTEM), user])
        report["narrative"] = resp.content
    except Exception as e:  # 叙述失败不影响客观统计输出
        report["narrative"] = f"（学情叙述生成失败：{e}）"
    return {"report": report, "steps": steps}
