"""题目↔考点多对多关联模型(附加考点)。

约定:`questions.knowledge_point_id` 是**主考点**(薄弱点统计、组卷归因,归因干净);
本表只存**附加考点**(一道题跨考的其他考点,RAG 追问时拉取全部关联考点语料),
不含主考点。附加考点不进薄弱点/组卷逻辑。

主考点 + 附加考点共用一个考点标签体系,两者各司其职。
"""
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QuestionKnowledgePoint(Base):
    __tablename__ = "question_knowledge_points"
    __table_args__ = (
        UniqueConstraint("question_id", "knowledge_point_id", name="uq_qkp_question_kp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"), index=True, nullable=False
    )
    knowledge_point_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_points.id"), index=True, nullable=False
    )

    def __repr__(self) -> str:
        return f"<QuestionKnowledgePoint q#{self.question_id} kp#{self.knowledge_point_id}>"
