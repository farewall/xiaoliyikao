"""用户相关 API。

MVP 阶段用微信 login code 换取 openid 并建号。
完整 wx 登录(校验 + 换取 openid)需要调用微信接口,此处先以 code 占位,
真正的 code2session 调用在部署接入微信时补齐。
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginResponse, UserLoginRequest, UserOut
from app.services.auth import create_token

router = APIRouter(prefix="/users", tags=["users"])


async def exchange_code_for_openid(code: str) -> str:
    """调用微信 code2session 换取 openid。

    需在配置中提供 WECHAT_APPID / WECHAT_SECRET 才会真正调用微信;
    未配置时(开发期)用 code 本身作为测试 openid,便于本地联调。
    """
    if not settings.wechat_appid or not settings.wechat_secret:
        # 开发占位:固定 openid,让本地联调复用同一用户(贴近生产行为)
        return "dev-openid"

    url = "https://api.weixin.qq.com/sns/jscode2session"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            params={
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        data = resp.json()
        openid = data.get("openid")
        if not openid:
            raise HTTPException(status_code=400, detail=f"微信登录失败: {data.get('errmsg', '未知错误')}")
        return openid


@router.post("/login", response_model=LoginResponse)
async def login(payload: UserLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """登录:code 换 openid,查/建用户,签发 JWT(token)。"""
    openid = await exchange_code_for_openid(payload.code)

    user = db.query(User).filter(User.openid == openid).first()
    if user is None:
        user = User(openid=openid)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token(user)
    return LoginResponse(token=token, user=UserOut.model_validate(user))
