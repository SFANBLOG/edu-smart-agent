from __future__ import annotations

"""FastAPI 应用入口（仅提供后端 API）。

前后端分离：
- 开发期：前端 Vite（默认 5173）通过 proxy 把 /api 转发到本服务；
- 生产期：`npm run build` 产出 frontend/dist，若存在则由本服务托管为 SPA。

运行：
    uvicorn app.main:app --reload --port 8000
或：
    python -m app.main
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.config import get_settings

# 前端构建产物目录：backend/app/main.py -> ../../frontend/dist
SPA_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title=s.app_name,
        description=(
            "AI批改 · 错题分析 · 学情分析 · 智能辅导 多智能体后端"
            "（FastAPI + LangChain + LangGraph + Agent + 多模态）"
        ),
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    # 生产期：若已构建前端，则托管 dist 作为单页应用（开发期由 Vite 提供）
    if SPA_DIST.exists():
        app.mount(
            "/assets", StaticFiles(directory=str(SPA_DIST / "assets")), name="spa-assets"
        )

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            # 交给前端路由（history 模式回退到 index.html）
            return FileResponse(str(SPA_DIST / "index.html"))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    s = get_settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=True)
