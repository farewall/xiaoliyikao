"""AI 使用配额模型。

免费层每日 AI 追问次数上限(见讨论记录 Q7/Q8)。
按 (user_id, date) 唯一,每次追问原子自增,超限拒绝 —— 亏损天花板锁死。
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIUsage(Base):
    __tablename__ = "ai_usages"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_ai_usage_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
