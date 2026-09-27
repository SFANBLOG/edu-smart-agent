from __future__ import annotations

"""REST 路由。

端点：
- POST /api/grade          上传作业图片 -> AI批改 + 错题分析 + 入库
- POST /api/analytics      学情分析报告
- GET  /api/errors         查询错题本明细（可按学生）
- GET  /api/health         健康检查 / 能力探测
"""

from base64 import b64encode

from fastapi import APIRouter, File, Form, UploadFile

from app.config import get_settings
from app.db import get_store
from app.service import run_analytics, run_grading
from app.service.schemas import (
    AgentResponse,
    AnalyticsRequest,
    GradeRequest,
    ImageInput,
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


@router.get("/errors")
def errors(student_id: str | None = None, limit: int = 100):
    return {"errors": get_store().list_errors(student_id=student_id, limit=limit)}
