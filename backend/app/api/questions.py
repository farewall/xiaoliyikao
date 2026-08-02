"""刷题相关 API。

MVP 版刷题:
- 组卷:按考点/章节/科目取随机题。
- 提交答案:判分 + 记录答题 + 返回解析(答完立刻看解析,是刷题闭环的一环)。
"""
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.models.user import User
from app.schemas.question import AnswerResult, AnswerSubmit, QuestionOut, QuizRequest
from app.services.auth import get_current_user

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/quiz", response_model=list[QuestionOut])
def create_quiz(
    payload: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Question]:
    """组一套题。可空参数:默认取全库随机题。

    按 subject/chapter 过滤时,经考点表(knowledge_points)联查。
    """
    stmt = select(Question)

    if payload.subject or payload.chapter or payload.knowledge_point_id:
        stmt = stmt.join(KnowledgePoint, Question.knowledge_point_id == KnowledgePoint.id)
        if payload.subject:
            stmt = stmt.where(KnowledgePoint.subject == payload.subject)
        if payload.chapter:
            stmt = stmt.where(KnowledgePoint.chapter == payload.chapter)
        if payload.knowledge_point_id:
            stmt = stmt.where(KnowledgePoint.id == payload.knowledge_point_id)

    rows = db.execute(stmt).scalars().all()
    random.shuffle(rows)
    return rows[: payload.count]


@router.post("/answer", response_model=AnswerResult)
def submit_answer(
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnswerResult:
    """提交答案,判分并记录。"""
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    user_answer = sorted(payload.user_answer)
    correct_answer = sorted(question.answer)
    is_correct = user_answer == correct_answer

    # 答题记录归属当前登录用户
    record = AnswerRecord(
        user_id=current_user.id,
        question_id=question.id,
        user_answer=user_answer,
        is_correct=is_correct,
        duration_seconds=payload.duration_seconds,
    )
    db.add(record)
    db.commit()

    return AnswerResult(
        question_id=question.id,
        is_correct=is_correct,
        correct_answer=question.answer,
        explanation=question.explanation,
    )
