"""会话模型(练习 / 模拟测试)。

统一承载两类"一轮作答":
- kind=practice:练习会话,结束时一次性落库,供「练习记录 / 该轮错题回顾」。
- kind=mock:模拟测试会话,考试中持续更新进度(题目/答案/剩余时间),
  支撑「中断续考」;交卷时判分出报告。

答题明细(薄弱点 / 每日统计)仍由 answer_records 聚合,本表只记录"这一轮"的
题目构成与作答结果,两者各司其职。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StudySession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # practice / mock
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="practice")
    # in_progress / completed / abandoned
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="in_progress")

    # 组卷配置:{subject?|subjects?|count/paper_type|knowledge_point_id?}
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # 题目 id 列表(按出场顺序)
    question_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # 作答明细:[{question_id, user_answer, duration_seconds, is_correct}]
    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # 进行中位置(练习不用;模拟续考用)
    current_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 剩余时间(秒),仅 mock
    remaining_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # mock 交卷后的报告(成绩/估分/各科正确率)
    report: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<StudySession {self.kind}/{self.status} #{self.id}>"
