"""数据库连接与会话管理。

使用 SQLAlchemy 2.0 风格。

MVP 阶段不依赖 pgvector(向量检索为预留能力,见 models/question.py 注释)。
如需启用,在服务器上安装 pgvector 扩展后,把 config 里的 EMBEDDING_ENABLED 置为 true。
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖:请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
