"""AI 答疑相关请求/响应模型。"""
from pydantic import BaseModel


class AIAskRequest(BaseModel):
    question_id: int
    user_question: str  # 用户针对该题的追问
    user_answer: list[str] | None = None  # 用户本题所选答案,便于 AI 解释"为什么错"


class AIAskResponse(BaseModel):
    answer: str
    # 引用来源(文档片段 ID 或标题),体现 RAG「有依据、可溯源」
    references: list[str] = []
    quota_remaining: int | None = None  # 今日剩余免费次数
