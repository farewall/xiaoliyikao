"""题目模型。

题目是产品的核心实体。设计要点:
- 题干/选项/答案存 JSON,支持单选、多选、A3/A4 病例题等 306 常见题型。
- explanation 为 AI 基于医学知识自主重写的解析(不录入出版物原文,见讨论记录 Q5)。
- 每题归一个题组(question_groups,见 ADR 0004):独立题 1:1;A3/A4、B 型子题 1:N,
  共享内容(病例/选项池)存题组一行,组内顺序用 position 显式保证。

MVP 阶段不启用向量检索(embedding 字段移除)。
将来做语义检索/相似题推荐时,需要:安装 pgvector 扩展 + 在本题增加
`embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)` 字段。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 所属题组(独立题组 1:1;病例/池子题共用一组)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("question_groups.id"), index=True, nullable=False
    )
    # 组内顺序(1,2,3…),显式排序;删除重插不乱序
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # 题型:single 单选 / multiple 多选 / case 病例分析(A3/A4)
    qtype: Mapped[str] = mapped_column(String(16), index=True, nullable=False)

    stem: Mapped[str] = mapped_column(Text, nullable=False)  # 题干(子题时为纯问句)
    # 选项;A1/A2/X 独立题、A3/A4 子题有;B 型子题为空(取组的池)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    answer: Mapped[list] = mapped_column(JSONB, nullable=False)  # ["A"] 或 ["A","C"]
    explanation: Mapped[str] = mapped_column(Text, nullable=False)  # AI 自主重写的解析

    # 考点标签(薄弱点分析与 RAG 的共同地基)
    knowledge_point_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_points.id"), index=True, nullable=True
    )

    # 来源与年份(真题溯源,可选)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 如:真题 2023
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 题组关系(前端块状渲染用;共享内容/顺序见 question_groups)
    group: Mapped["QuestionGroup"] = relationship("QuestionGroup")
