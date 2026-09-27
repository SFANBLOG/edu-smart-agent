from __future__ import annotations

"""冒烟测试：无需大模型密钥，验证应用装配、路由、管线降级与存储层统计。

运行：pytest -q
"""

from fastapi.testclient import TestClient

from app.db import Store
from app.main import app
from app.models import ErrorRecord, GradingResult, QuestionGrade

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "llm_enabled" in body


def test_store_aggregation(tmp_path):
    """验证错题本与学情统计的 SQL 聚合（含知识点掌握度、错误类型分布、平均分）。"""
    db = tmp_path / "test.db"
    store = Store(str(db))

    grading = GradingResult(
        subject="数学",
        total_score=100,
        earned_score=70,
        questions=[
            QuestionGrade(question_no="1", is_correct=True, score=10, max_score=10, knowledge_point="函数"),
            QuestionGrade(question_no="2", is_correct=False, score=0, max_score=10, knowledge_point="导数"),
            QuestionGrade(question_no="3", is_correct=False, score=0, max_score=20, knowledge_point="导数"),
        ],
    )
    store.save_grading("stu1", grading)
    store.save_errors([
        ErrorRecord(student_id="stu1", subject="数学", question_no="2", knowledge_point="导数", error_type="概念不清"),
        ErrorRecord(student_id="stu1", subject="数学", question_no="3", knowledge_point="导数", error_type="计算失误"),
    ])

    summary = store.summary_stats()
    assert summary["total_gradings"] == 1
    assert summary["total_errors"] == 2
    assert 0.6 <= summary["avg_score_rate"] <= 0.75

    mastery = store.knowledge_mastery()
    daoshu = next(m for m in mastery if m["knowledge_point"] == "导数")
    assert daoshu["wrong"] == 2
    assert daoshu["attempts"] == 2

    dist = store.error_type_dist()
    assert dist["概念不清"] == 1 and dist["计算失误"] == 1

    # 单知识点过滤也不应报错（覆盖 WHERE 拼接修复）
    only_math = store.knowledge_mastery(subject="数学")
    assert isinstance(only_math, list)


def test_grade_pipeline_degrades_without_key():
    """未配置密钥时，批改链应安全返回占位结果而非 500。"""
    r = client.post(
        "/api/grade",
        json={"images": [], "student_id": "t1", "reference": ""},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["task"] == "grade"
    assert "grading" in body


def test_analytics_endpoint():
    r = client.post("/api/analytics", json={"student_id": None, "subject": None})
    assert r.status_code == 200
    body = r.json()
    assert body["report"] is not None
    assert "knowledge_mastery" in body["report"]
