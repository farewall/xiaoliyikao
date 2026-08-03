"""刷题相关 API。

- 组卷:按考点/章节/科目/多科范围取随机题。
- 提交答案:判分 + 记录答题 + 返回解析(答完立刻看解析,是刷题闭环的一环)。
- 题目详情:记录详情页用(题干/选项/答案/解析)。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.models.user import User
from app.schemas.question import AnswerResult, AnswerSubmit, QuestionDetail, QuestionOut, QuizRequest
from app.services.auth import get_current_user
from app.services.question_bank import pick_questions

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/quiz", response_model=list[QuestionOut])
def create_quiz(
    payload: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Question]:
    """组一套题。可空参数:默认取全库随机题。"""
    questions = pick_questions(
        db,
        subjects=payload.subjects,
        subject=payload.subject,
        chapter=payload.chapter,
        knowledge_point_id=payload.knowledge_point_id,
        question_ids=payload.question_ids,
        count=payload.count,
    )
    return questions


@router.get("/subjects")
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """有题目的科目列表(配置页数据源)。"""
    rows = (
        db.query(KnowledgePoint.subject)
        .join(Question, Question.knowledge_point_id == KnowledgePoint.id)
        .distinct()
        .order_by(KnowledgePoint.subject)
        .all()
    )
    return [r[0] for r in rows]


@router.get("/{question_id}", response_model=QuestionDetail)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
    """题目详情(含答案与解析)。记录详情页用,答题后查看。"""
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question


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
