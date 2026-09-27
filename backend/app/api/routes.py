from __future__ import annotations

"""REST 路由。

端点：
- POST /api/grade          上传作业图片 -> AI批改 + 错题分析 + 入库
- POST /api/analytics      学情分析报告
- POST /api/tutor          苏格拉底式辅导对话（结合错因启发）
- POST /api/recommend      基于薄弱知识点的个性化智能推题
- POST /api/review         错题间隔复习调度（拉到期队列 / 回写已复习）
- GET  /api/errors         查询错题本明细（可按学生）
- GET  /api/health         健康检查 / 能力探测
"""

from base64 import b64encode

from fastapi import APIRouter, File, Form, UploadFile

from app.config import get_settings
from app.db import get_store
from app.service import (
    run_analytics,
    run_grading,
    run_recommend,
    run_review,
    run_tutor,
)
from app.service.schemas import (
    AgentResponse,
    AnalyticsRequest,
    GradeRequest,
    ImageInput,
    RecommendRequest,
    ReviewRequest,
    TutorRequest,
)

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    s = get_settings()
    return {
        "status": "ok",
        "app": s.app_name,
        "llm_enabled": s.llm_enabled,
        "vlm_model": s.vlm_model,
        "llm_model": s.llm_model,
    }


@router.post("/grade", response_model=AgentResponse)
async def grade(req: GradeRequest):
    return await run_grading(req)


@router.post("/grade/upload")
async def grade_upload(
    file: UploadFile = File(...),
    student_id: str = Form("anonymous"),
    reference: str = Form(""),
):
    """直接上传一张作业图片进行批改（自动转 base64 data URL）。"""
    raw = await file.read()
    data_url = f"data:{file.content_type or 'image/png'};base64," + b64encode(raw).decode()
    req = GradeRequest(
        images=[ImageInput(base64=data_url)], student_id=student_id, reference=reference
    )
    return await run_grading(req)


@router.post("/analytics", response_model=AgentResponse)
async def analytics(req: AnalyticsRequest):
    return await run_analytics(req)


@router.post("/tutor", response_model=AgentResponse)
async def tutor(req: TutorRequest):
    """苏格拉底式辅导：传入学生本轮提问与历史，返回一句启发。"""
    return await run_tutor(req)


@router.post("/recommend", response_model=AgentResponse)
async def recommend(req: RecommendRequest):
    """针对该生薄弱知识点，生成个性化变式练习计划。"""
    return await run_recommend(req)


@router.post("/review", response_model=AgentResponse)
async def review(req: ReviewRequest):
    """拉取到期复习队列；传入 review_ids 则先回写已复习再返回新队列。"""
    return await run_review(req)


@router.get("/errors")
def errors(student_id: str | None = None, limit: int = 100):
    return {"errors": get_store().list_errors(student_id=student_id, limit=limit)}
