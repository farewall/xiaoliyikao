"""会话(练习 / 模拟测试)相关请求/响应模型。"""
from datetime import datetime

from pydantic import BaseModel

from app.schemas.question import QuestionOut


class QuestionAnswer(BaseModel):
    """一道题的作答。

    客户端提交时可不带 is_correct(服务端统一判分);
    输出时服务端补上判分结果。
    """
    question_id: int
    user_answer: list[str]
    duration_seconds: int | None = None
    is_correct: bool | None = None


class MockStartRequest(BaseModel):
    """开始一次模拟测试。

    subjects 为空 = 全科;paper_type 为题量(卷型 30/60/180)。
    """
    subjects: list[str] = []
    paper_type: int = 30


class MockProgressRequest(BaseModel):
    """模拟进行中同步进度。status='abandoned' 表示用户放弃本次。"""
    current_index: int = 0
    remaining_seconds: int | None = None
    answers: list[QuestionAnswer] = []
    status: str | None = None


class MockSubmitRequest(BaseModel):
    """交卷:提交全部作答与剩余时间。"""
    remaining_seconds: int | None = None
    answers: list[QuestionAnswer]


class PracticeCompleteRequest(BaseModel):
    """练习结束:提交本轮题目构成与作答,落一条完成的练习会话。

    config 由前端按场景构造:{subject, count} 或 {knowledge_point_id, count}。
    """
    config: dict
    answers: list[QuestionAnswer]


class MockStartResponse(BaseModel):
    session_id: int
    questions: list[QuestionOut]
    remaining_seconds: int


class SessionListItem(BaseModel):
    """历史列表项:派生 correct_count / total_count。"""
    id: int
    kind: str
    status: str
    config: dict
    started_at: datetime
    finished_at: datetime | None = None
    correct_count: int = 0
    total_count: int = 0
    report: dict | None = None

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    """会话详情(续考 / 回看):题目展开 + 作答明细 + 报告。"""
    id: int
    kind: str
    status: str
    config: dict
    question_ids: list[int]
    answers: list[QuestionAnswer] = []
    current_index: int = 0
    remaining_seconds: int | None = None
    report: dict | None = None
    started_at: datetime
    finished_at: datetime | None = None
    questions: list[QuestionOut] = []

    model_config = {"from_attributes": True}
