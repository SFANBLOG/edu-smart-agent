from __future__ import annotations

"""生成演示数据：直接向 SQLite 写入若干批改记录与错题，
即使未配置大模型密钥，也能在「学情分析」页看到统计效果。

运行：python scripts/seed_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_store  # noqa: E402
from app.models import ErrorRecord, GradingResult, QuestionGrade  # noqa: E402

DEMO = [
    ("stu_A", "数学", [
        ("1", True, "函数", 10, 10), ("2", False, "导数", 0, 10),
        ("3", False, "导数", 0, 10), ("4", True, "数列", 8, 8),
    ]),
    ("stu_A", "数学", [
        ("1", False, "圆锥曲线", 0, 12), ("2", True, "导数", 10, 10),
    ]),
    ("stu_B", "物理", [
        ("1", False, "牛顿第二定律", 0, 10), ("2", False, "动能定理", 3, 12),
        ("3", True, "动量守恒", 10, 10),
    ]),
    ("stu_B", "物理", [
        ("1", False, "牛顿第二定律", 0, 10), ("2", True, "万有引力", 8, 8),
    ]),
]

ERR_TYPE = ["概念不清", "计算失误", "方法不会", "审题偏差"]


def main() -> None:
    store = get_store()
    for i, (sid, subject, qs) in enumerate(DEMO):
        questions = []
        total = earned = 0
        for no, ok, kp, sc, mx in qs:
            total += mx
            earned += sc
            questions.append(
                QuestionGrade(
                    question_no=no, is_correct=ok, knowledge_point=kp,
                    score=sc, max_score=mx,
                    feedback="" if ok else f"{kp} 掌握不牢",
                )
            )
        g = GradingResult(
            subject=subject, total_score=total, earned_score=earned,
            questions=questions, overall_comment="演示数据",
        )
        store.save_grading(sid, g)
        errs = [
            ErrorRecord(
                student_id=sid, subject=subject, question_no=q.question_no,
                knowledge_point=q.knowledge_point, error_type=ERR_TYPE[(i + j) % len(ERR_TYPE)],
                cause="演示错因", suggestion="针对性练习该知识点",
            )
            for j, q in enumerate(questions) if not q.is_correct
        ]
        store.save_errors(errs)
    print("演示数据已写入。可启动服务后打开『学情分析』查看。")


if __name__ == "__main__":
    main()
