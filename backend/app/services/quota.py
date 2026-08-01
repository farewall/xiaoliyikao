"""AI 配额服务。

免费层每日追问次数上限;付费解锁后为付费用户跳过限额。
用行锁(select_for_update)保证同一用户并发请求时计数不丢失。
"""
from datetime import date

from sqlalchemy.orm import Session

from app.config import settings
from app.models.quota import AIUsage


class QuotaExceededError(Exception):
    """免费配额已用完。"""


def get_today_usage(db: Session, user_id: int) -> AIUsage:
    today = date.today()
    usage = (
        db.query(AIUsage)
        .filter(AIUsage.user_id == user_id, AIUsage.usage_date == today)
        .first()
    )
    if usage is None:
        usage = AIUsage(user_id=user_id, usage_date=today, count=0)
        db.add(usage)
        db.flush()
    return usage


def get_remaining(db: Session, user_id: int, is_paid: bool = False) -> int:
    """今日剩余次数。付费用户返回 -1(表示不限)。"""
    if is_paid:
        return -1
    usage = get_today_usage(db, user_id)
    return max(0, settings.free_ai_quota_per_day - usage.count)


def consume(db: Session, user_id: int, is_paid: bool = False) -> int:
    """消耗一次配额,返回剩余次数。超限抛 QuotaExceededError。"""
    if is_paid:
        return -1
    usage = (
        db.query(AIUsage)
        .filter(AIUsage.user_id == user_id, AIUsage.usage_date == date.today())
        .with_for_update()
        .first()
    )
    if usage is None:
        usage = AIUsage(user_id=user_id, usage_date=date.today(), count=0)
        db.add(usage)
        db.flush()

    if usage.count >= settings.free_ai_quota_per_day:
        raise QuotaExceededError("今日免费追问次数已用完")

    usage.count += 1
    db.flush()
    return settings.free_ai_quota_per_day - usage.count
