"""应用配置。

所有配置项均可通过环境变量覆盖,默认值面向本地开发。
生产环境请通过 .env / 环境变量注入。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    app_name: str = "小鲤医考"
    app_env: str = "development"  # development / production
    debug: bool = True

    # 数据库
    database_url: str = "postgresql+psycopg2://xiaoliyikao:你的密码@localhost:5432/xiaoliyikao_dev"

    # DeepSeek (OpenAI 兼容接口)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # 免费层 AI 配额(每日追问次数上限)
    free_ai_quota_per_day: int = 5

    # 微信登录(code2session 换 openid)
    wechat_appid: str = ""
    wechat_secret: str = ""

    # 登录态(JWT 签名密钥;生产务必替换为强随机串)
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_expire_days: int = 7

    # CORS(开发期允许小程序调试)
    cors_origins: list[str] = ["*"]


settings = Settings()
