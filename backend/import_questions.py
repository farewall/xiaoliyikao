# -*- coding: utf-8 -*-
"""批量导入真题(CSV) → questions 表,自动建考点。

用法(backend/ 下):
    .venv/Scripts/python.exe import_questions.py 题库.csv

CSV 格式(首行表头,UTF-8 带 BOM 可用 Excel/WPS 直接编辑):
    题目,选项A,选项B,选项C,选项D,选项E,答案,解析,学科,章节,考点,题型,来源,年份
    - 一行一题;选项留空表示没有该项(最多 A-E)
    - 答案如 "A" 或 "A,C";题型 single/multiple/case(默认 single)
    - 解析可先留空(可后补),学科/章节/考点必填

行为:
    - 考点不存在 → 自动新建(subject/chapter/name,description 留空由语料后补)
    - 考点已存在 → 复用
    - 题干已存在 → 跳过(防重复导入)
"""
import csv
import sys
from pathlib import Path

from app.database import SessionLocal
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.models.question_group import QuestionGroup

OPTION_KEYS = ["A", "B", "C", "D", "E"]
QTYPES = ("single", "multiple", "case")


def parse_answer(raw: str) -> list:
    """'A,C' / 'AC' / 'a c' → ['A','C']"""
    return [c.upper() for c in raw if c.isalpha() and c.upper() in OPTION_KEYS]


def get_or_create_kp(db, subject: str, chapter: str, name: str) -> KnowledgePoint:
    kp = (
        db.query(KnowledgePoint)
        .filter_by(subject=subject, chapter=chapter, name=name)
        .first()
    )
    if kp is None:
        kp = KnowledgePoint(subject=subject, chapter=chapter, name=name)
        db.add(kp)
        db.flush()
    return kp


def import_csv(db, path: Path) -> None:
    created = skipped = errors = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):  # 第 1 行是表头
            try:
                stem = (row.get("题目") or "").strip()
                if not stem:
                    errors += 1
                    print(f"[第{lineno}行] 跳过:题目为空")
                    continue
                if db.query(Question).filter(Question.stem == stem).first():
                    skipped += 1
                    print(f"[第{lineno}行] 跳过:题干已存在")
                    continue

                options = {}
                for k in OPTION_KEYS:
                    v = (row.get(f"选项{k}") or "").strip()
                    if v:
                        options[k] = v
                answer = parse_answer(row.get("答案") or "")
                if not options or not answer:
                    errors += 1
                    print(f"[第{lineno}行] 跳过:选项或答案缺失")
                    continue

                subject = (row.get("学科") or "").strip()
                chapter = (row.get("章节") or "").strip()
                name = (row.get("考点") or "").strip()
                if not (subject and chapter and name):
                    errors += 1
                    print(f"[第{lineno}行] 跳过:学科/章节/考点缺失")
                    continue

                kp = get_or_create_kp(db, subject, chapter, name)
                qtype = (row.get("题型") or "single").strip()
                year_raw = (row.get("年份") or "").strip()

                # 每题归一个 single 独立题组(题组方案见 ADR 0004)
                group = QuestionGroup(kind="single")
                db.add(group)
                db.flush()
                db.add(
                    Question(
                        group_id=group.id,
                        position=1,
                        qtype=qtype if qtype in QTYPES else "single",
                        stem=stem,
                        options=options,
                        answer=answer,
                        explanation=(row.get("解析") or "").strip(),
                        knowledge_point_id=kp.id,
                        source=(row.get("来源") or "").strip() or None,
                        year=int(year_raw) if year_raw.isdigit() else None,
                    )
                )
                created += 1
            except Exception as e:  # noqa: BLE001 - 单行失败不阻断批量
                errors += 1
                print(f"[第{lineno}行] 出错: {e}")
    db.commit()
    print(f"导入完成: 新增题目 {created}, 跳过重复 {skipped}, 失败 {errors}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"文件不存在: {path}")
        sys.exit(1)
    db = SessionLocal()
    try:
        import_csv(db, path)
    finally:
        db.close()


if __name__ == "__main__":
    main()
