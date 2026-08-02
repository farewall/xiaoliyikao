"""AI 答疑 API。

核心差异化能力:针对题目的追问答疑(RAG + DeepSeek)。
配额控制:免费层每日限次,超限返回 402。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.ai import AIAskRequest, AIAskResponse
from app.services.auth import get_current_user
from app.services.quota import QuotaExceededError, consume, get_remaining
from app.services.rag import RAGService

router = APIRouter(prefix="/ai", tags=["ai"])

rag_service = RAGService()


@router.post("/ask", response_model=AIAskResponse)
def ask(
    payload: AIAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIAskResponse:
    """针对某道题的追问答疑。消费一次免费配额。"""
    # 1. 配额检查 + 消耗
    try:
        remaining = consume(db, current_user.id)
    except QuotaExceededError as e:
        raise HTTPException(status_code=402, detail=str(e)) from e

    # 2. RAG 答疑
    try:
        answer, references = rag_service.ask(db, payload.question_id, payload.user_question)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        db.rollback()  # 配额计数回滚,不让失败请求吃掉免费次数
        raise HTTPException(status_code=503, detail=str(e)) from e

    db.commit()
    return AIAskResponse(answer=answer, references=references, quota_remaining=remaining)


@router.get("/quota", response_model=dict)
def quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """查询今日剩余免费追问次数。"""
    remaining = get_remaining(db, current_user.id)
    return {"quota_remaining": remaining}
