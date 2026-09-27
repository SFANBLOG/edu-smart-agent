from __future__ import annotations

"""调用 LangGraph 管线：批改链 / 学情链。

用 astream(stream_mode="updates") 逐节点执行，既能收集真实执行顺序，
又便于将来扩展 SSE 流式。这里聚合成一次性响应返回。
"""

from app.agents.graph import get_pipeline
from app.agents.state import PipelineState
from app.service.schemas import (
    AgentResponse,
    AnalyticsRequest,
    GradeRequest,
    RecommendRequest,
    ReviewRequest,
    TutorRequest,
)


def _thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}


async def _run(state: PipelineState, thread_id: str) -> PipelineState:
    pipeline = get_pipeline()
    steps: list[str] = []
    final: PipelineState = state
    async for event in pipeline.astream(
        state.model_dump(), config=_thread_config(thread_id), stream_mode="updates"
    ):
        for node_name, update in event.items():
            steps.append(node_name)
            # 合并节点产出到 final 状态
            data = final.model_dump()
            data.update(update or {})
            data["steps"] = steps
            final = PipelineState(**data)
    final.steps = steps
    return final


async def run_grading(req: GradeRequest) -> AgentResponse:
    state = PipelineState(
        task="grade",
        student_id=req.student_id,
        images=[img.to_data_url() for img in req.images],
        reference=req.reference,
    )
    final = await _run(state, thread_id=f"grade:{req.student_id}")
    return AgentResponse(
        task="grade",
        student_id=req.student_id,
        grading=final.grading,
        error_analysis=final.error_analysis,
        saved_errors=final.saved_errors,
        steps=final.steps,
        error=final.error,
    )


async def run_analytics(req: AnalyticsRequest) -> AgentResponse:
    state = PipelineState(
        task="analytics",
        student_id=req.student_id or "anonymous",
        subject=req.subject,
    )
    final = await _run(
        state, thread_id=f"analytics:{req.student_id or 'all'}:{req.subject or 'all'}"
    )
    return AgentResponse(
        task="analytics",
        student_id=req.student_id or "anonymous",
        report=final.report,
        steps=final.steps,
    )


async def run_tutor(req: TutorRequest) -> AgentResponse:
    state = PipelineState(
        task="tutor",
        student_id=req.student_id,
        question=req.question,
        history=req.history,
    )
    final = await _run(state, thread_id=f"tutor:{req.student_id}")
    return AgentResponse(
        task="tutor",
        student_id=req.student_id,
        tutor_reply=final.tutor_reply,
        steps=final.steps,
    )


async def run_recommend(req: RecommendRequest) -> AgentResponse:
    state = PipelineState(
        task="recommend",
        student_id=req.student_id,
        subject=req.subject,
        top_k=req.top_k,
    )
    final = await _run(state, thread_id=f"recommend:{req.student_id}")
    return AgentResponse(
        task="recommend",
        student_id=req.student_id,
        practice_plan=final.practice_plan,
        steps=final.steps,
    )


async def run_review(req: ReviewRequest) -> AgentResponse:
    state = PipelineState(
        task="review",
        student_id=req.student_id or "anonymous",
        review_ids=req.review_ids,
    )
    final = await _run(
        state, thread_id=f"review:{req.student_id or 'all'}"
    )
    return AgentResponse(
        task="review",
        student_id=req.student_id or "anonymous",
        review_queue=final.review_queue,
        reviewed=final.reviewed,
        steps=final.steps,
    )
