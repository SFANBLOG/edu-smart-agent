from __future__ import annotations

"""AI 批改 Agent（多模态）。

输入学生作业图片（URL / base64 data URL），用支持视觉的大模型读取图片，
以 GradingResult 作为结构化输出 schema，得到逐题判分 + 知识点标注的批改结果。

未配置密钥时返回可预期的占位结果，保证流水线与前端在无 Key 下仍可演示。
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import GRADING_SYSTEM
from app.agents.state import PipelineState
from app.config import get_settings
from app.core.llm import get_vlm
from app.models import GradingResult


def _build_user_content(state: PipelineState) -> list:
    content: list = [
        {"type": "text", "text": "请批改图片中的作业/试卷，并按要求的 JSON 结构输出结果。"}
    ]
    if state.reference:
        content.append(
            {"type": "text", "text": f"【参考答案/评分标准】{state.reference}"}
        )
    for url in state.images:
        content.append({"type": "image_url", "image_url": {"url": url}})
    return content


async def grading_node(state: PipelineState) -> dict:
    s = get_settings()
    steps = ["grading"]

    if not s.llm_enabled:
        placeholder = GradingResult(
            subject="",
            total_score=0,
            earned_score=0,
            questions=[],
            overall_comment="（未配置 OPENAI_API_KEY，AI 批改已跳过。请配置密钥后重试。）",
        )
        return {"grading": placeholder, "steps": steps, "error": "no_api_key"}

    if not state.images:
        empty = GradingResult(overall_comment="未收到作业图片，无法批改。")
        return {"grading": empty, "steps": steps, "error": "no_image"}

    structured = get_vlm().with_structured_output(GradingResult)
    messages = [
        SystemMessage(content=GRADING_SYSTEM),
        HumanMessage(content=_build_user_content(state)),
    ]
    result: GradingResult = await structured.ainvoke(messages)
    return {"grading": result, "steps": steps}
