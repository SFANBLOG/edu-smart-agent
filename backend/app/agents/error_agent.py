from __future__ import annotations

"""错题分析 Agent + 入库节点。

- error_node  : 从批改结果中挑出错误题，用文本大模型做归因（错误类型/错因/建议）。
- persist_node: 把批改结果与错题本记录写入 SQLite，供学情统计长期积累。

无错题或无密钥时安全跳过 LLM，仅做客观落库。
"""

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.agents.prompts import ERROR_SYSTEM
from app.agents.state import PipelineState
from app.config import get_settings
from app.core.llm import get_llm
from app.db import get_store
from app.models import ErrorAnalysis, ErrorRecord, GradingResult


class _WrongInput(BaseModel):
    """喂给归因模型的错题条目。"""

    question_no: str
    knowledge_point: str = ""
    student_answer: str = ""
    correct_answer: str = ""
    feedback: str = ""


def _wrong_questions(grading: GradingResult) -> list:
    return [q for q in grading.questions if not q.is_correct]


async def error_node(state: PipelineState) -> dict:
    steps = ["error_analysis"]
    grading = state.grading
    if grading is None:
        return {"error_analysis": ErrorAnalysis(), "steps": steps}

    wrongs = _wrong_questions(grading)
    if not wrongs:
        return {
            "error_analysis": ErrorAnalysis(summary="本次没有错题，全部答对。"),
            "steps": steps,
        }

    if not get_settings().llm_enabled:
        # 无密钥：给出基于批改正误的朴素归因，保证链路可用
        items = [
            {
                "question_no": q.question_no,
                "knowledge_point": q.knowledge_point,
                "error_type": "其他",
                "cause": q.feedback or "答错（未配置密钥，暂无深度归因）。",
                "suggestion": "建议订正并复盘相关知识点。",
            }
            for q in wrongs
        ]
        analysis = ErrorAnalysis(errors=items, summary=f"共 {len(wrongs)} 道错题。")
        return {"error_analysis": analysis, "steps": steps}

    structured = get_llm().with_structured_output(ErrorAnalysis)
    payload = [
        _WrongInput(
            question_no=q.question_no,
            knowledge_point=q.knowledge_point,
            student_answer=q.student_answer,
            correct_answer=q.correct_answer,
            feedback=q.feedback,
        ).model_dump()
        for q in wrongs
    ]
    import json

    user = HumanMessage(
        content=f"以下是本次批改判为错误的题目，请逐题归因：\n{json.dumps(payload, ensure_ascii=False)}"
    )
    analysis: ErrorAnalysis = await structured.ainvoke([SystemMessage(content=ERROR_SYSTEM), user])
    return {"error_analysis": analysis, "steps": steps}


async def persist_node(state: PipelineState) -> dict:
    """把批改结果与错题落库。"""
    steps = ["persist"]
    store = get_store()
    grading = state.grading
    saved = 0
    if grading is not None:
        store.save_grading(state.student_id, grading)
        analysis = state.error_analysis
        # question_no -> 归因条目
        emap = {}
        if analysis:
            for it in analysis.errors:
                emap[it.question_no] = it
        records = []
        for q in _wrong_questions(grading):
            it = emap.get(q.question_no)
            records.append(
                ErrorRecord(
                    student_id=state.student_id,
                    subject=grading.subject,
                    question_no=q.question_no,
                    knowledge_point=q.knowledge_point,
                    error_type=(it.error_type if it else "其他"),
                    student_answer=q.student_answer,
                    correct_answer=q.correct_answer,
                    cause=(it.cause if it else q.feedback),
                    suggestion=(it.suggestion if it else ""),
                )
            )
        saved = store.save_errors(records)
    return {"saved_errors": saved, "steps": steps}
