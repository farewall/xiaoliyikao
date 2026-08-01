"""题目相关请求/响应模型。"""
from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: int
    qtype: str
    stem: str
    options: dict
    knowledge_point_id: int | None = None
    source: str | None = None
    year: int | None = None

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: int
    user_answer: list[str]
    duration_seconds: int | None = None


class AnswerResult(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: list[str]
    explanation: str  # 答完立刻返回解析


class QuestionWithExplanation(QuestionOut):
    explanation: str


class QuizRequest(BaseModel):
    """生成一套题的请求。

    - 按考点组卷:knowledge_point_id 或 (subject, chapter)
    - 按科目刷题:subject 可选
    - count: 题量
    """
    subject: str | None = None
    chapter: str | None = None
    knowledge_point_id: int | None = None
    count: int = 10
