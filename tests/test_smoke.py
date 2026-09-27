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


def test_review_scheduling(tmp_path):
    """验证错题入库后排期、到期队列与已复习回写（遗忘曲线递进）。"""
    from datetime import datetime, timedelta

    store = Store(str(tmp_path / "rev.db"))
    store.save_errors([
        ErrorRecord(student_id="s1", subject="数学", question_no="1",
                    knowledge_point="导数", error_type="概念不清")
    ])
    # 新入库默认 1 天后到期，今天不应出现在队列
    assert store.due_reviews(student_id="s1") == []

    # 手动排为已到期
    past = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    with store._conn() as c:
        c.execute("UPDATE error_records SET next_review_at=?", (past,))
    due = store.due_reviews(student_id="s1")
    assert len(due) == 1 and due[0]["overdue_days"] >= 1

    # 标记已复习：review_count+1，下次到期向后推，今天不再到期
    eid = due[0]["id"]
    assert store.mark_reviewed([eid]) == 1
    row = store.list_errors("s1")[0]
    assert row["review_count"] == 1
    assert row["next_review_at"] > datetime.now().strftime("%Y-%m-%d")
    assert store.due_reviews(student_id="s1") == []


def test_errors_by_weak_points(tmp_path):
    store = Store(str(tmp_path / "weak.db"))
    store.save_errors([
        ErrorRecord(student_id="s1", subject="数学", question_no="1",
                    knowledge_point="导数", error_type="概念不清"),
        ErrorRecord(student_id="s1", subject="数学", question_no="2",
                    knowledge_point="数列", error_type="计算失误"),
    ])
    got = store.errors_by_weak_points(["导数"], student_id="s1")
    assert len(got) == 1 and got[0]["knowledge_point"] == "导数"


def test_new_endpoints_degrade_without_key():
    """未配置密钥时，辅导/推题/复习端点均应 200 并返回对应产物字段。"""
    r = client.post("/api/tutor", json={"student_id": "t1", "question": "这道导数题怎么做"})
    assert r.status_code == 200
    assert r.json()["tutor_reply"] is not None

    r = client.post("/api/recommend", json={"student_id": "t1", "top_k": 3})
    assert r.status_code == 200
    assert r.json()["practice_plan"] is not None

    r = client.post("/api/review", json={"student_id": "t1"})
    assert r.status_code == 200
    assert "review_queue" in r.json()
