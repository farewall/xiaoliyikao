"""用户相关请求/响应模型。"""
from pydantic import BaseModel


class UserLoginRequest(BaseModel):
    code: str  # 微信 wx.login 返回的临时凭证


class UserOut(BaseModel):
    id: int
    nickname: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class WeakPoint(BaseModel):
    """薄弱点聚合结果。"""
    subject: str
    chapter: str
    knowledge_point_id: int
    knowledge_point_name: str
    wrong_count: int
    total_count: int
    accuracy: float  # 正确率 0~1
