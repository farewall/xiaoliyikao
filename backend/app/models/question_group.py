"""题组模型(练习/组卷/展示的单位,见 ADR 0004)。

题组承载一块题的**共享内容**与**组内顺序**,三种 kind:
- `single`:独立题(单选/多选),与题目 1:1,无共享内容
- `case`:A3/A4 共享病例,`scenario` 存病例文本,子题 `stem` 存纯问句、各自有 `options`
- `pool`:B 型共用选项池,`options` 存池,子题 `options` 为空(渲染时取池)

判分/薄弱点/错题按小题(见 questions / answer_records),题组不参与判分。
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QuestionGroup(Base):
    __tablename__ = "question_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # single / case(A3/A4) / pool(B型)
    kind: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    # A3/A4 共享病例(仅 case)
    scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    # B 型共用选项池(仅 pool)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<QuestionGroup {self.kind} #{self.id}>"
