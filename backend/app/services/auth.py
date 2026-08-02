"""自定义登录态:JWT 签发与校验。

流程(见讨论记录):
1. 前端 wx.login 拿 code,POST /users/login。
2. 后端 code2session 换 openid,查/建用户。
3. 签发 JWT(token)返回前端,前端每次请求带 Authorization: Bearer <token>。
4. 受保护接口通过 get_current_user 依赖校验 token,识别出当前用户。

JWT 采用 HS256 对称签名,密钥来自 settings.jwt_secret(生产务必换强随机串)。
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

ALGORITHM = "HS256"


def create_token(user: User) -> str:
    """为指定用户签发 JWT。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),  # subject:用户 id
        "iat": now,  # 签发时间
        "exp": now + timedelta(days=settings.jwt_expire_days),  # 过期时间
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI 依赖:从 Authorization 头解析 token,返回当前用户。

    401 场景统一返回「未登录」,前端收到后清 token 并重新走登录流程。
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期,请重新登录") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="登录凭证无效") from None

    user_id = int(payload.get("sub"))
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
