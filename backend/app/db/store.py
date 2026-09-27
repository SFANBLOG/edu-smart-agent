from __future__ import annotations

"""SQLite 持久化层：批改记录 + 错题本 + 学情统计聚合。

设计要点：
- 纯标准库 sqlite3，零外部依赖，开箱即用；
- 学情统计（知识点掌握度、错误类型分布、平均得分率）全部用 SQL 聚合完成，
  即使未配置大模型密钥也能产出客观数据，LLM 仅额外补充自然语言洞察；
- 过滤条件支持 student_id / subject，服务"个人 / 全班 / 单科"多口径学情。
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.config import get_settings
from app.models import ErrorRecord, GradingResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS gradings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT,
    total_score REAL,
    earned_score REAL,
    score_rate REAL,
    result_json TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS error_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT,
    question_no TEXT,
    knowledge_point TEXT,
    error_type TEXT,
    student_answer TEXT,
    correct_answer TEXT,
    cause TEXT,
    suggestion TEXT,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_review_at TEXT,
    next_review_at TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_err_stu ON error_records(student_id);
CREATE INDEX IF NOT EXISTS idx_err_kp ON error_records(knowledge_point);
"""

# 艾宾浩斯遗忘曲线：按已复习次数递进的复习间隔（天）
_REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30]


class Store:
    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        with self._conn() as c:
            c.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        """兼容旧库：为已存在的 error_records 补充复习调度列。"""
        want = {
            "review_count": "INTEGER NOT NULL DEFAULT 0",
            "last_review_at": "TEXT",
            "next_review_at": "TEXT",
        }
        with self._conn() as c:
            cols = {r["name"] for r in c.execute("PRAGMA table_info(error_records)")}
            for col, ddl in want.items():
                if col not in cols:
                    c.execute(f"ALTER TABLE error_records ADD COLUMN {col} {ddl}")
            # 历史上未排期的错题，用 created_at 初始化为“创建次日到期”
            c.execute(
                "UPDATE error_records SET next_review_at = "
                "date(created_at, '+1 day') "
                "WHERE next_review_at IS NULL AND created_at IS NOT NULL"
            )
            # 新列就位后再建到期索引（不能放进 _SCHEMA，否则旧库会先于建列引用到它）
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_err_due ON error_records(next_review_at)"
            )

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------- 写入 ----------------
    def save_grading(self, student_id: str, result: GradingResult) -> int:
        total = result.total_score or sum(q.max_score for q in result.questions)
        earned = result.earned_score or sum(q.score for q in result.questions)
        rate = (earned / total) if total else 0.0
        now = datetime.now().isoformat(timespec="seconds")
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO gradings(student_id, subject, total_score, earned_score,"
                " score_rate, result_json, created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    student_id,
                    result.subject,
                    total,
                    earned,
                    rate,
                    result.model_dump_json(),
                    now,
                ),
            )
            return cur.lastrowid

    def save_errors(self, records: List[ErrorRecord]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        first_due = (datetime.now() + timedelta(days=_REVIEW_INTERVALS[0])).strftime(
            "%Y-%m-%d"
        )
        rows = [
            (
                r.student_id, r.subject, r.question_no, r.knowledge_point,
                r.error_type, r.student_answer, r.correct_answer,
                r.cause, r.suggestion, 0, None, first_due, now,
            )
            for r in records
        ]
        if not rows:
            return 0
        with self._conn() as c:
            c.executemany(
                "INSERT INTO error_records(student_id, subject, question_no,"
                " knowledge_point, error_type, student_answer, correct_answer,"
                " cause, suggestion, review_count, last_review_at, next_review_at,"
                " created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
        return len(rows)

    # ---------------- 查询 / 聚合 ----------------
    def _where(self, student_id: Optional[str], subject: Optional[str]):
        clauses, params = [], []
        if student_id:
            clauses.append("student_id=?")
            params.append(student_id)
        if subject:
            clauses.append("subject=?")
            params.append(subject)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, params

    def knowledge_mastery(
        self, student_id: Optional[str] = None, subject: Optional[str] = None, top: int = 20
    ) -> List[dict]:
        """按知识点统计 考查次数与错误次数，计算掌握率。

        考查次数 = 该知识点在批改中出现的题目总数（对+错），
        错误次数 = 错题本中该知识点记录数。
        """
        clauses = ["knowledge_point<>''"]
        params: list = []
        base_where, base_params = self._where(student_id, subject)
        # base_where 形如 " WHERE a=? AND b=?"，拆出条件并入
        if base_where:
            clauses.append(base_where[len(" WHERE "):])
            params.extend(base_params)
        where_sql = " WHERE " + " AND ".join(clauses)
        with self._conn() as c:
            # 错误次数：错题本中每个知识点的记录数
            rows = c.execute(
                f"SELECT knowledge_point, COUNT(*) AS wrong FROM error_records{where_sql}"
                " GROUP BY knowledge_point ORDER BY wrong DESC LIMIT 500",
                params,
            ).fetchall()
        # 尝试从批改记录中还原每个知识点的总考查次数
        attempts_map = self._knowledge_attempts(student_id, subject)
        out = []
        for r in rows:
            kp = r["knowledge_point"]
            attempts = attempts_map.get(kp, r["wrong"]) or r["wrong"]
            out.append(
                {
                    "knowledge_point": kp,
                    "attempts": attempts,
                    "wrong": r["wrong"],
                    "mastery_rate": round(1 - r["wrong"] / attempts, 4) if attempts else 0.0,
                }
            )
        return out[:top]

    def _knowledge_attempts(
        self, student_id: Optional[str], subject: Optional[str]
    ) -> dict:
        where, params = self._where(student_id, subject)
        with self._conn() as c:
            rows = c.execute(
                f"SELECT result_json FROM gradings{where}", params
            ).fetchall()
        from collections import Counter

        counter: Counter = Counter()
        for row in rows:
            try:
                data = json.loads(row["result_json"])
            except Exception:
                continue
            for q in data.get("questions", []):
                kp = (q.get("knowledge_point") or "").strip()
                if kp:
                    counter[kp] += 1
        return dict(counter)

    def error_type_dist(
        self, student_id: Optional[str] = None, subject: Optional[str] = None
    ) -> dict:
        where, params = self._where(student_id, subject)
        with self._conn() as c:
            rows = c.execute(
                f"SELECT error_type, COUNT(*) AS n FROM error_records{where}"
                " GROUP BY error_type",
                params,
            ).fetchall()
        return {r["error_type"] or "未分类": r["n"] for r in rows}

    def summary_stats(
        self, student_id: Optional[str] = None, subject: Optional[str] = None
    ) -> dict:
        where, params = self._where(student_id, subject)
        with self._conn() as c:
            g = c.execute(
                f"SELECT COUNT(*) AS n, AVG(score_rate) AS avg_rate FROM gradings{where}",
                params,
            ).fetchone()
            e_where, e_params = self._where(student_id, subject)
            e = c.execute(
                f"SELECT COUNT(*) AS n FROM error_records{e_where}", e_params
            ).fetchone()
        return {
            "total_gradings": g["n"] or 0,
            "total_errors": e["n"] or 0,
            "avg_score_rate": round(g["avg_rate"] or 0.0, 4),
        }

    def list_errors(self, student_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        where, params = self._where(student_id, None)
        params.append(limit)
        with self._conn() as c:
            rows = c.execute(
                f"SELECT * FROM error_records{where} ORDER BY id DESC LIMIT ?", params
            ).fetchall()
        return [dict(r) for r in rows]

    def errors_by_weak_points(
        self, points: List[str], student_id: Optional[str] = None, per_point: int = 3
    ) -> List[dict]:
        """按薄弱知识点拉取典型错题（供智能推题作为变式依据）。"""
        out: List[dict] = []
        with self._conn() as c:
            for kp in points:
                clauses = ["knowledge_point=?"]
                params: list = [kp]
                if student_id:
                    clauses.append("student_id=?")
                    params.append(student_id)
                rows = c.execute(
                    "SELECT * FROM error_records WHERE "
                    + " AND ".join(clauses)
                    + " ORDER BY id DESC LIMIT ?",
                    params + [per_point],
                ).fetchall()
                out.extend(dict(r) for r in rows)
        return out

    # ---------------- 间隔复习调度 ----------------
    def due_reviews(
        self, student_id: Optional[str] = None, limit: int = 50
    ) -> List[dict]:
        """返回已到期（next_review_at <= 今天）的待复习错题，逾期越久越优先。"""
        today = datetime.now().strftime("%Y-%m-%d")
        clauses = ["next_review_at<=?"]
        params: list = [today]
        if student_id:
            clauses.append("student_id=?")
            params.append(student_id)
        params.append(limit)
        with self._conn() as c:
            rows = c.execute(
                "SELECT *, CAST(julianday(?) - julianday(next_review_at) AS INTEGER)"
                " AS overdue_days FROM error_records WHERE "
                + " AND ".join(clauses)
                + " ORDER BY overdue_days DESC, next_review_at ASC LIMIT ?",
                [today] + params,
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_reviewed(self, error_ids: List[int]) -> int:
        """回写复习结果：已复习次数 +1，重排下一次到期日（按遗忘曲线递进）。"""
        if not error_ids:
            return 0
        today = datetime.now()
        n = 0
        with self._conn() as c:
            for eid in error_ids:
                row = c.execute(
                    "SELECT review_count FROM error_records WHERE id=?", (eid,)
                ).fetchone()
                if row is None:
                    continue
                new_count = (row["review_count"] or 0) + 1
                idx = min(new_count - 1, len(_REVIEW_INTERVALS) - 1)
                nxt = (today + timedelta(days=_REVIEW_INTERVALS[idx])).strftime("%Y-%m-%d")
                c.execute(
                    "UPDATE error_records SET review_count=?, last_review_at=?,"
                    " next_review_at=? WHERE id=?",
                    (new_count, today.isoformat(timespec="seconds"), nxt, eid),
                )
                n += 1
        return n


_store: Optional[Store] = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store(get_settings().db_path)
    return _store
