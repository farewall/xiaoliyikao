"""答题记录模型。

每答一题记一条,是「正确率」「薄弱点分析」的数据来源。
is_correct 与 knowledge_point_id 的组合支撑按考点聚合薄弱点。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnswerRecord(Base):
    __tablename__ = "answer_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True, nullable=False)

    user_answer: Mapped[list] = mapped_column(JSONB, nullable=False)  # 用户提交的选项
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # 作答耗时(秒),用于观察卡壳点(可选)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
