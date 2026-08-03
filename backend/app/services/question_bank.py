"""组卷服务:按范围从题库抽题。

练习/模拟/薄弱点直达共用的抽题逻辑:
- 多科范围:subjects=[生理学,...]
- 单科:subject="生理学"(兼容现有 quiz 参数)
- 考点直达:knowledge_point_id
- 章节:chapter(预留)
"""
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question


def pick_questions(
    db: Session,
    *,
    subjects: list[str] | None = None,
    subject: str | None = None,
    chapter: str | None = None,
    knowledge_point_id: int | None = None,
    question_ids: list[int] | None = None,
    count: int = 10,
) -> list[Question]:
    """按范围随机抽题,数量不足时返回现有全部(调用方自行决定是否提示)。

    question_ids 给定时不随机,按给定顺序返回(重练错题用)。
    """
    stmt = select(Question)

    if question_ids:
        rows = db.execute(stmt.where(Question.id.in_(question_ids))).scalars().all()
        by_id = {q.id: q for q in rows}
        return [by_id[i] for i in question_ids if i in by_id]

    if subjects:
        stmt = stmt.join(KnowledgePoint, Question.knowledge_point_id == KnowledgePoint.id)
        stmt = stmt.where(KnowledgePoint.subject.in_(subjects))
    elif subject or chapter or knowledge_point_id:
        stmt = stmt.join(KnowledgePoint, Question.knowledge_point_id == KnowledgePoint.id)
        if subject:
            stmt = stmt.where(KnowledgePoint.subject == subject)
        if chapter:
            stmt = stmt.where(KnowledgePoint.chapter == chapter)
        if knowledge_point_id:
            stmt = stmt.where(KnowledgePoint.id == knowledge_point_id)

    rows = db.execute(stmt).scalars().all()
    random.shuffle(rows)
    return rows[:count]
