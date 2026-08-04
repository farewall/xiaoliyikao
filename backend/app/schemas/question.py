"""题目相关请求/响应模型。"""
from pydantic import BaseModel


class QuestionGroupOut(BaseModel):
    """题组信息:前端块状渲染用(共享内容 + 组类型)。"""

    id: int
    kind: str  # single / case / pool
    scenario: str | None = None  # A3/A4 共享病例
    options: dict | None = None  # B 型共用选项池

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    group_id: int
    position: int
    qtype: str
    stem: str
    options: dict | None = None
    group: QuestionGroupOut | None = None
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


class QuestionDetail(QuestionOut):
    """记录详情用:题目 + 正确答案 + 解析(答题后才允许查看)。"""
    answer: list[str]
    explanation: str


class QuizRequest(BaseModel):
    """生成一套题的请求。

    - 按考点组卷:knowledge_point_id 或 (subject, chapter)
    - 按科目刷题:subject 可选
    - 按多科范围组卷:subjects(模拟测试用)
    - count: 题量
    """
    subject: str | None = None
    subjects: list[str] | None = None
    chapter: str | None = None
    knowledge_point_id: int | None = None
    question_ids: list[int] | None = None  # 指定题目(重练错题用),此时不随机
    count: int = 10
