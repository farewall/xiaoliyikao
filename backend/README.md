# 后端

FastAPI + PostgreSQL + DeepSeek RAG。医学考研 306 刷题后端。

## 快速开始(本地开发)

前置:本机安装 **Python 3.12+**,有可用的 PostgreSQL(本地或服务器)。

```bash
cd backend
python -m venv .venv                 # 创建虚拟环境(避免污染本机 Python 2.7)
# Windows: .venv\Scripts\activate   |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # 填入 DEEPSEEK_API_KEY 与 DATABASE_URL
uvicorn app.main:app --reload        # 启动
```

- 后端:http://localhost:8000
- 接口文档(Swagger):http://localhost:8000/docs
- 健康检查:http://localhost:8000/health

## 数据库说明

- MVP 阶段使用**普通 PostgreSQL**,**不依赖 pgvector**(向量检索为预留能力)。
- 将来做语义检索/相似题推荐时,再启用 pgvector(见 `models/question.py` 注释)。

## 常用命令

```bash
uvicorn app.main:app --reload   # 开发热重载
```

## 目录结构

```
app/
├── main.py          # FastAPI 入口,挂路由 + 建表
├── config.py        # 配置(环境变量可覆盖)
├── database.py      # SQLAlchemy 连接
├── models/          # ORM 模型
│   ├── user.py              # 用户
│   ├── knowledge_point.py   # 考点标签(三级)
│   ├── question.py          # 题目
│   ├── answer_record.py     # 答题记录
│   └── quota.py             # AI 配额
├── schemas/         # Pydantic 请求/响应
├── services/        # 业务逻辑
│   ├── rag.py       # RAG 答疑(核心差异化)
│   ├── quota.py     # 免费配额控制
│   └── weakness.py  # 薄弱点分析
└── api/             # 路由
    ├── users.py     # 登录
    ├── questions.py# 刷题(组卷/判分)
    ├── ai.py        # AI 追问答疑 + 配额
    └── weakness.py  # 薄弱点
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /health | 健康检查 |
| POST | /users/login | 登录(code 换 openid) |
| POST | /questions/quiz | 组一套题 |
| POST | /questions/answer | 提交答案,返回判分+解析 |
| POST | /ai/ask | 针对某题追问答疑(消耗配额) |
| GET | /ai/quota | 今日剩余追问次数 |
| GET | /weakness | 薄弱点清单 |

## 说明

- 开发期 `user_id` 以 1 占位,登录体系接入后替换。
- 启动时自动建表(MVP 阶段);生产环境迁移到 alembic。
- RAG 检索当前基于考点标签 + 题目上下文;向量检索接口已预留。
