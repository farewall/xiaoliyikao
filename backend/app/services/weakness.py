"""薄弱点分析服务。

按考点聚合答题记录,计算正确率,输出「薄弱点清单」。
薄弱点定义:作答次数 >= min_attempts 且正确率低于 threshold。
"""
from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from app.models.answer_record import AnswerRecord
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.schemas.user import WeakPoint


def analyze_weak_points(
    db: Session,
    user_id: int,
    min_attempts: int = 3,
    threshold: float = 0.6,
) -> list[WeakPoint]:
    """聚合用户各考点的作答统计,返回薄弱点列表(按正确率升序)。"""
    rows = (
        db.query(
            KnowledgePoint.id,
            KnowledgePoint.subject,
            KnowledgePoint.chapter,
            KnowledgePoint.name,
            func.count(AnswerRecord.id).label("total"),
            func.sum(func.cast(AnswerRecord.is_correct, Integer)).label("correct"),
        )
        .join(Question, Question.knowledge_point_id == KnowledgePoint.id)
        .join(AnswerRecord, AnswerRecord.question_id == Question.id)
        .filter(AnswerRecord.user_id == user_id)
        .group_by(KnowledgePoint.id, KnowledgePoint.subject, KnowledgePoint.chapter, KnowledgePoint.name)
        .all()
    )

    weak_points: list[WeakPoint] = []
    for r in rows:
        total = int(r.total)
        if total < min_attempts:
            continue  # 样本不足,不判定薄弱点
        correct = int(r.correct or 0)
        accuracy = correct / total
        if accuracy < threshold:
            weak_points.append(
                WeakPoint(
                    subject=r.subject,
                    chapter=r.chapter,
                    knowledge_point_id=r.id,
                    knowledge_point_name=r.name,
                    wrong_count=total - correct,
                    total_count=total,
                    accuracy=accuracy,
                )
            )

    weak_points.sort(key=lambda w: w.accuracy)
    return weak_points
