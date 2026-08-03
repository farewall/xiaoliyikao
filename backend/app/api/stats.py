"""学习统计 API。

首页状态条(今日已刷题数)与「我的」页统计(连续打卡 / 累计已刷题数)的数据源。
时间一律以数据库时区为准(answered_at 为 timestamptz)。
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


def _compute_streak(db: Session, user_id: int, today: date) -> int:
    """连续打卡天数:从今天(或昨天)起向前数连续有答题记录的天数。"""
    rows = (
        db.query(func.date(AnswerRecord.answered_at).label("d"))
        .filter(AnswerRecord.user_id == user_id)
        .distinct()
        .all()
    )
    day_set = {r[0] for r in rows}
    if not day_set:
        return 0

    # 从今天或昨天开始算连续
    start = today if today in day_set else today - timedelta(days=1)
    if start not in day_set:
        return 0

    streak = 0
    d = start
    while d in day_set:
        streak += 1
        d -= timedelta(days=1)
    return streak


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """今日答题数 / 累计答题数 / 连续打卡天数。"""
    today: date = db.execute(select(func.current_date())).scalar()

    today_count = (
        db.query(func.count(AnswerRecord.id))
        .filter(
            AnswerRecord.user_id == current_user.id,
            func.date(AnswerRecord.answered_at) == today,
        )
        .scalar()
    )
    total_count = (
        db.query(func.count(AnswerRecord.id))
        .filter(AnswerRecord.user_id == current_user.id)
        .scalar()
    )

    return {
        "today_count": today_count or 0,
        "total_count": total_count or 0,
        "streak_days": _compute_streak(db, current_user.id, today),
    }
