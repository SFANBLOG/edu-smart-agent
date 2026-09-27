# AI 批改 · 错题分析 · 学情分析系统

> **FastAPI + LangChain + LangGraph + Agent + 多模态大模型** 实现的教育智能体系统。
> 教师上传学生作业图片 → 多模态大模型**逐题批改** → 自动**错题归因** → 沉淀**错题本** →
> 聚合产出**学情分析报告**（客观统计 + AI 教学洞察）。

---

## ✨ 三大核心功能

| 功能 | 说明 | 关键技术 |
|------|------|---------|
| 📸 **AI 批改** | 读取作业/试卷图片，识别作答、判对错、逐题打分、标注知识点、给评语 | 多模态视觉模型 + `with_structured_output` 结构化输出 |
| 📕 **错题分析** | 从批改结果挑出错题，按错误类型归因（概念/计算/审题/方法…）并给订正建议，落库错题本 | 文本推理模型 + SQLite 持久化 |
| 📊 **学情分析** | 聚合平均得分率、知识点掌握度、错误类型分布、薄弱点，生成 AI 教学建议 | SQL 客观统计（无需 Key）+ LLM 洞察叙述 |

---

## 🧭 架构：LangGraph 多智能体管线

```
                       ┌─────────────────────── LangGraph ───────────────────────┐
  教师端(浏览器)         │                                                          │
 ┌──────────┐  HTTP     │   START ──(按 task 路由)──┐                              │
 │ 作业图片  │──────────▶│                           ├─ "grade" ─▶ [grading]        │
 │ 文字请求  │           │                           │              │ 多模态批改     │
 └──────────┘           │                           │              ▼               │
                        │                           │           [error] 错题归因    │
                        │                           │              ▼               │
                        │                           │           [persist] 落库      │
                        │                           │              ▼               │
                        │                           │              END             │
                        │                           │                              │
                        │                           └─ "analytics" ─▶ [stats]       │
                        │                                            │  SQL 聚合     │
                        │                                            ▼             │
                        │                                         [report] AI洞察  │
                        │                                            ▼             │
                        │                                           END             │
                        └──────────────────────────────────────────────────────────┘
                                       │
              ┌────────────┬───────────┼────────────┬──────────────┐
              ▼            ▼           ▼            ▼              ▼
        多模态VLM      文本LLM      SQLite 存储    MemorySaver    FastAPI
       (qwen-vl)    (归因/报告)   批改记录+错题本   会话记忆      REST 服务
```

- **批改链 (grade)**：`grading → error → persist` —— 图片经多模态模型结构化批改，错题归因后写入数据库，长期积累学情数据。
- **学情链 (analytics)**：`stats → report` —— 先用纯 SQL 聚合客观指标（**无密钥也能出统计**），再让大模型补充自然语言洞察。
- **checkpointer**：`MemorySaver` 按 `thread_id` 维护会话上下文。
- **优雅降级**：未配置密钥时批改链返回占位结果、学情链仍产出客观统计，全流程不崩溃。

---

## 📁 目录结构

```
edu-smart-agent/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置(pydantic-settings)
│   ├── core/llm.py             # 多模态VLM / 文本LLM 工厂
│   ├── models/                 # 领域模型：批改结果/错题/学情报告
│   ├── db/store.py             # SQLite：批改记录+错题本+SQL统计
│   ├── agents/
│   │   ├── state.py            # LangGraph 状态(task 路由)
│   │   ├── prompts.py          # 批改/归因/学情 提示词
│   │   ├── grading_agent.py    # AI批改节点(多模态+结构化输出)
│   │   ├── error_agent.py      # 错题归因 + 落库节点
│   │   ├── analytics_agent.py  # 学情统计 + AI报告节点
│   │   └── graph.py            # LangGraph 管线装配
│   ├── service/                # 请求模型 + 调用管线
│   └── api/routes.py           # REST 端点
├── static/index.html           # 教师端(批改/错题本/学情 三栏)
├── scripts/seed_demo.py        # 演示数据(无Key也能看学情)
├── tests/test_smoke.py         # 冒烟测试(无需密钥)
├── requirements.txt / .env.example
└── README.md
```

---

## 🚀 快速开始

```bash
cd edu-smart-agent
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt

copy .env.example .env        # 填入 OPENAI_API_KEY 等
```

> 💡 **换国内多模态大模型零改码**：已在 `.env` 用 **阿里通义 DashScope**（`qwen-vl-plus` +
> `https://dashscope.aliyuncs.com/compatible-mode/v1`）验证可跑通。GLM-4V、文心等 OpenAI 兼容接口同理，
> 只需替换 `OPENAI_BASE_URL` / `VLM_MODEL` / `LLM_MODEL`。

启动：
```bash
# （可选）灌入演示数据，未配置Key也能看学情分析
python scripts/seed_demo.py

uvicorn app.main:app --reload --port 8000
```
- 教师端：http://localhost:8000/
- 接口文档：http://localhost:8000/docs

---

## 🔌 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/health` | 健康检查与能力探测 |
| POST | `/api/grade` | JSON 传入图片(base64/url) → 批改 + 错题分析 + 落库 |
| POST | `/api/grade/upload` | 直接上传一张作业图片批改（multipart） |
| POST | `/api/analytics` | 学情分析报告（可按 student_id / subject 过滤） |
| GET  | `/api/errors` | 查询错题本明细 |

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

- `pytest -q` → **4 passed**（应用装配、存储 SQL 聚合、批改链降级、学情端点）
- 端到端实测：配置真实 DashScope 密钥后，`/api/analytics` 执行 `['stats','report']`，
  客观统计（知识点掌握度 / 错误类型分布 / 薄弱点排序）正确，且 **AI 学情洞察 narrative 真实生成成功**。

---

## 🛠 常见问题

- **批改无反应 / 返回占位？** 检查 `.env` 是否填 `OPENAI_API_KEY`，`/api/health` 的 `llm_enabled` 应为 `true`。
- **图片识别不准？** `VLM_MODEL` 必须是支持图像输入的模型（如 `qwen-vl-plus`、`gpt-4o`）；纯文本模型会忽略图片。
- **学情没数据？** 先批改入库或运行 `python scripts/seed_demo.py` 灌演示数据。
- **错题本/学情数据来源？** 全部来自 `data/edu.db`（SQLite），可持久累积、支持个人/全班/单科多口径统计。

---

## 📌 说明

- 参考的微信文章链接因平台反爬无法抓取正文；本系统按指定技术栈
  （**FastAPI + LangChain + LangGraph + Agent + 多模态**）针对「AI批改 / 错题分析 / 学情分析」场景完整实现。
- 生产化建议：`MemorySaver` 换 Postgres checkpointer；`/api` 加鉴权与限流；
  错题本按学校/班级多租户隔离；批改结果增加人工复核回写。
