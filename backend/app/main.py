"""FastAPI 应用入口。

挂载全部路由,提供健康检查。启动时自动建表(开发期用,MVP 后再上 alembic 迁移)。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import ai, questions, users, weakness
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发期自动建表;生产环境切换为 alembic 迁移
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(questions.router)
app.include_router(ai.router)
app.include_router(weakness.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
