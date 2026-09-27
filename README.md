# AI 批改 · 错题分析 · 学情分析 · 智能辅导系统

> **前后端分离的多智能体教育系统**：后端 **FastAPI + LangChain + LangGraph + Agent + 多模态大模型**，
> 前端 **Vue3 + Vite + TypeScript + Element Plus + Pinia**。
> 教师上传学生作业图片 → 多模态大模型**逐题批改** → 自动**错题归因** → 沉淀**错题本** →
> 聚合产出**学情分析报告**；并对学生提供**苏格拉底式辅导**、**薄弱点智能推题**、**遗忘曲线复习调度**。

---

## 📦 代码仓库（双平台镜像）

| 平台 | 地址 | git 远端 |
|------|------|---------|
| Gitee | https://gitee.com/BLOGSFan/edu-smart-agent | `origin` |
| GitHub | https://github.com/SFANBLOG/edu-smart-agent | `github` |

一次提交同步推送两端：

```bash
git push origin master ; git push github master
```

---

## ✨ 六大核心功能

| 功能 | 说明 | 关键技术 |
|------|------|---------|
| 📸 **AI 批改** | 读取作业/试卷图片，识别作答、判对错、逐题打分、标注知识点、给评语 | 多模态视觉模型 + `with_structured_output` 结构化输出 |
| 📕 **错题分析** | 从批改结果挑出错题，按错误类型归因（概念/计算/审题/方法…）并给订正建议，落库错题本 | 文本推理模型 + SQLite 持久化 |
| 📊 **学情分析** | 聚合平均得分率、知识点掌握度、错误类型分布、薄弱点，生成 AI 教学建议 | SQL 客观统计（无需 Key）+ LLM 洞察叙述 |
| 💡 **AI 辅导** | 面向学生的多轮对话，结合其错题落点做苏格拉底式启发，不直接报答案 | 会话历史 + 薄弱点接地（grounding） |
| 🎯 **智能推题** | 定位掌握率最低的知识点，据典型错题改编同类变式题，含提示与推荐理由 | 图路由 + 结构化出题（无 Key 回推错题重做） |
| ⏰ **复习调度** | 按艾宾浩斯遗忘曲线（1/2/4/7/15/30 天）排期，拉取到期清单、一键回写已复习 | 确定性调度（无需大模型，随时可用） |

---

## 🧭 架构：LangGraph 多智能体管线

```
                     ┌───────────────── LangGraph（按 task 路由）─────────────────┐
 教师/学生端(Vue3)    │                                                             │
┌───────────┐ HTTP   │  START ┬─ "grade"     ▶ [grading] ▶ [error] ▶ [persist] ▶ END │
│ 作业图片   │───────▶│        ├─ "analytics" ▶ [stats]   ▶ [report]          ▶ END  │
│ 文字/提问  │        │        ├─ "tutor"     ▶ [tutor]                       ▶ END  │
└───────────┘        │        ├─ "recommend" ▶ [recommend]                    ▶ END  │
                     │        └─ "review"    ▶ [review]                       ▶ END  │
                     └─────────────────────────────────────────────────────────────┘
                                     │
             ┌───────────┬───────────┼───────────┬──────────────┐
             ▼           ▼           ▼           ▼              ▼
       多模态VLM     文本LLM      SQLite 存储   MemorySaver    FastAPI
      (qwen-vl)  (归因/报告/    批改+错题+     会话记忆       REST 服务
                  辅导/推题)     复习排期
```

> 五条按 `task` 路由的子链：`grade`（批改→归因→落库）、`analytics`（统计→洞察）、
> `tutor`（辅导对话）、`recommend`（智能推题）、`review`（复习调度），各链执行完即 END。

- **批改链 (grade)**：`grading → error → persist` —— 图片经多模态模型结构化批改，错题归因后写入数据库，长期积累学情数据。
- **学情链 (analytics)**：`stats → report` —— 先用纯 SQL 聚合客观指标（**无密钥也能出统计**），再让大模型补充自然语言洞察。
- **辅导链 (tutor)**：读取该生薄弱知识点作为接地 → 多轮启发式对话（无密钥时降级为模板启发）。
- **推题链 (recommend)**：从错题本定位薄弱点 → 取典型错题作变式依据 → 生成变式练习计划（无密钥时回推错题重做）。
- **复习链 (review)**：基于错题本上的 `review_count/next_review_at` 做确定性排期，拉到期清单/回写已复习，**无需大模型**。
- **checkpointer**：`MemorySaver` 按 `thread_id` 维护会话上下文。
- **优雅降级**：未配置密钥时批改链返回占位结果、学情链仍产出客观统计、推题回推错题、复习链完全可用，全流程不崩溃。

---

## 📁 目录结构

```
edu-smart-agent/
├── backend/                        # 后端：FastAPI + LangGraph 多智能体
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口（API + 可选托管前端 dist）
│   │   ├── config.py               # 配置(pydantic-settings，含 CORS 白名单)
│   │   ├── core/llm.py             # 多模态VLM / 文本LLM 工厂
│   │   ├── models/                 # 领域模型：批改结果/错题/学情报告/推题/复习
│   │   ├── db/store.py             # SQLite：批改记录+错题本(含复习排期)+SQL统计
│   │   ├── agents/
│   │   │   ├── state.py            # LangGraph 状态(task 路由)
│   │   │   ├── prompts.py          # 批改/归因/学情/辅导/推题 提示词
│   │   │   ├── grading_agent.py    # AI批改节点(多模态+结构化输出)
│   │   │   ├── error_agent.py      # 错题归因 + 落库节点
│   │   │   ├── analytics_agent.py  # 学情统计 + AI报告节点
│   │   │   ├── tutor_agent.py      # 苏格拉底式辅导对话节点
│   │   │   ├── recommend_agent.py  # 薄弱点智能推题节点
│   │   │   ├── review_agent.py     # 间隔复习调度节点(确定性)
│   │   │   └── graph.py            # LangGraph 管线装配(五路路由)
│   │   ├── service/                # 请求模型 + 调用管线
│   │   └── api/routes.py           # REST 端点
│   ├── scripts/seed_demo.py        # 演示数据(无Key也能看学情)
│   ├── tests/test_smoke.py         # 冒烟测试(无需密钥)
│   └── requirements.txt / .env.example
├── frontend/                       # 前端：Vue3 + Vite + TS + Element Plus + Pinia
│   ├── index.html / vite.config.ts # Vite 配置（/api proxy → 后端8000）
│   ├── package.json / tsconfig.json
│   └── src/
│       ├── main.ts / App.vue       # 应用入口
│       ├── api/                    # axios 客户端 + 端点封装
│       ├── types/                  # 与后端 Pydantic 对齐的 TS 类型
│       ├── stores/app.ts           # Pinia：全局学生标识 + 健康探测
│       ├── router/index.ts         # 六功能路由
│       ├── layouts/MainLayout.vue  # 侧边导航 + 顶栏
│       └── views/                  # 批改/错题本/学情/辅导/推题/复习 六视图
└── README.md
```

---

## 🚀 快速开始

项目分为 **`backend/`（FastAPI 多智能体）** 与 **`frontend/`（Vue3）** 两部分，开发期分别启动。

### 1. 后端（API 服务，默认 8000）

```bash
cd edu-smart-agent/backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt

copy .env.example .env        # 填入 OPENAI_API_KEY 等
python scripts/seed_demo.py   # （可选）灌演示数据，未配置Key也能看学情
uvicorn app.main:app --reload --port 8000
```

> 💡 **换国内多模态大模型零改码**：已在 `.env` 用 **阿里通义 DashScope**（`qwen-vl-plus` +
> `https://dashscope.aliyuncs.com/compatible-mode/v1`）验证可跑通。GLM-4V、文心等 OpenAI 兼容接口同理，
> 只需替换 `OPENAI_BASE_URL` / `VLM_MODEL` / `LLM_MODEL`。

- 接口文档：http://localhost:8000/docs

### 2. 前端（Vue 开发服务器，默认 5173）

```bash
cd edu-smart-agent/frontend
npm install
npm run dev
```

- 教师/学生端：http://localhost:5173
- Vite 已将 `/api` 代理到后端 8000，无需单独配置密钥（由后端统一持有）。

### 3. 生产部署（可选：单进程托管）

```bash
cd frontend && npm run build      # 产出 frontend/dist
cd ../backend && uvicorn app.main:app --port 8000   # 自动托管 dist 为 SPA
```

构建后，后端会将 `frontend/dist` 作为单页应用托管，仅需一个进程即可同时提供 API 与页面。

---

## 🔌 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/health` | 健康检查与能力探测 |
| POST | `/api/grade` | JSON 传入图片(base64/url) → 批改 + 错题分析 + 落库 |
| POST | `/api/grade/upload` | 直接上传一张作业图片批改（multipart） |
| POST | `/api/analytics` | 学情分析报告（可按 student_id / subject 过滤） |
| POST | `/api/tutor` | 苏格拉底式辅导对话（传入 question + history，返回一句启发） |
| POST | `/api/recommend` | 基于薄弱知识点的个性化变式推题（可传 top_k / subject） |
| POST | `/api/review` | 拉取到期复习队列；传 review_ids 则先回写已复习再返回新队列 |
| GET  | `/api/errors` | 查询错题本明细（含复习次数字段） |

**批改请求示例**：
```bash
curl -X POST http://localhost:8000/api/grade -H "Content-Type: application/json" \
  -d '{"images":[{"base64":"data:image/jpeg;base64...."}],"student_id":"stu_A","reference":"1.B 2.C"}'
```

**学情请求示例**：
```bash
curl -X POST http://localhost:8000/api/analytics -H "Content-Type: application/json" \
  -d '{"student_id":null,"subject":"数学"}'
```

---

## ✅ 验证状态

- `pytest -q`（于 `backend/`）→ **7 passed**（应用装配、存储 SQL 聚合、批改链降级、学情端点、
  复习排期与回写、薄弱点取数、辅导/推题/复习端点无密钥降级）
- 前端 `npm run build`（`vue-tsc` 类型检查 + Vite 打包）产出 `frontend/dist`，后端可单进程托管。
- 端到端实测：配置真实 DashScope 密钥后，`/api/analytics` 执行 `['stats','report']`，
  客观统计（知识点掌握度 / 错误类型分布 / 薄弱点排序）正确，且 **AI 学情洞察 narrative 真实生成成功**。
- 本地旧库兼容：`Store` 启动时自动迁移 `error_records` 新增 `review_count/last_review_at/next_review_at` 列并建索引。

---

## 🛠 常见问题

- **批改无反应 / 返回占位？** 检查 `.env` 是否填 `OPENAI_API_KEY`，`/api/health` 的 `llm_enabled` 应为 `true`。
- **图片识别不准？** `VLM_MODEL` 必须是支持图像输入的模型（如 `qwen-vl-plus`、`gpt-4o`）；纯文本模型会忽略图片。
- **学情没数据？** 先批改入库或运行 `python scripts/seed_demo.py` 灌演示数据。
- **错题本/学情数据来源？** 全部来自 `data/edu.db`（SQLite），可持久累积、支持个人/全班/单科多口径统计。

---

## 📌 说明

- 参考的微信文章链接因平台反爬无法抓取正文；本系统按指定技术栈
  （**FastAPI + LangChain + LangGraph + Agent + 多模态**）实现。
- 功能广度参考同类教育 Agent（Khanmigo 引导式辅导、松鼠AI Weak-point 推题、
  遗忘曲线错题本等）的标志性能力，在学生侧扩展了**辅导 / 推题 / 复习调度**三条链。
- 生产化建议：`MemorySaver` 换 Postgres checkpointer；`/api` 加鉴权与限流；
  错题本按学校/班级多租户隔离；批改结果增加人工复核回写。
