"""考点标签模型。

考点标签是「薄弱点分析」和「RAG 答疑」的共同地基:
- 薄弱点:按考点聚合错题,找出哪些考点弱。
- RAG:题目 → 考点 → 检索相关解析/知识片段。

结构:按 306 考纲组织,subject -> chapter -> point 三级。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 三级结构:学科 -> 章节 -> 考点
    subject: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # 如:生理学
    chapter: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # 如:循环系统
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # 如:房颤

    # 父级考点(可选,用于细分),null 表示顶级考点
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_points.id"), nullable=True)

    # 该考点的权威知识点讲解(AI 答疑的 RAG 语料之一)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<KnowledgePoint {self.subject}/{self.chapter}/{self.name}>"
