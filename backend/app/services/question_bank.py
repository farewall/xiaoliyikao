"""组卷服务:按范围从题库抽题。

练习/模拟/薄弱点直达共用的抽题逻辑:
- 多科范围:subjects=[生理学,...]
- 单科:subject="生理学"(兼容现有 quiz 参数)
- 考点直达:knowledge_point_id
- 章节:chapter(预留)

抽题以**题组**为单位(ADR 0004):随机打乱题组、整块加入,组内按 position 排序,
按小题计数,到目标即停(整块加入可略超,宁多勿拆)。返回的题目带 group 关系
(前端块状渲染用)。
"""
import random

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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
    """按范围抽题,以题组为单位(整块必进),数量不足时返回现有全部。

    - 随机分支(subjects/subject/chapter/考点):以**题组**为抽样单位随机打乱,整块加入,
      组内按 position 排序;按小题计数,到 count 即停(整块加入可略超,宁多勿拆)。
    - question_ids 给定时不随机、不按块扩展,按给定顺序返回(重练错题,精确重做)。
    """
    stmt = select(Question).options(selectinload(Question.group))

    if question_ids:
        rows = db.execute(stmt.where(Question.id.in_(question_ids))).scalars().all()
        by_id = {q.id: q for q in rows}
        return [by_id[i] for i in question_ids if i in by_id]

    if count <= 0:
        return []

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
    if not rows:
        return []

    # 以题组为抽样单位:组内按 position 排序,随机打乱题组,整块加入直到到目标
    groups: dict[int, list[Question]] = {}
    for q in rows:
        groups.setdefault(q.group_id, []).append(q)
    for qs in groups.values():
        qs.sort(key=lambda q: (q.position, q.id))

    group_ids = list(groups.keys())
    random.shuffle(group_ids)

    picked: list[Question] = []
    for gid in group_ids:
        picked.extend(groups[gid])
        if len(picked) >= count:
            break
    return picked
