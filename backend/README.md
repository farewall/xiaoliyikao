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

## 内容生产工具(录题 → 补解析 → 写语料)

> 三个离线脚本,与运行时无关;每个都有「人工审校」关口——医学内容审校后再入库。

| 工具 | 职责 | 用法 |
|---|---|---|
| `import_questions.py` | 录题:CSV → `questions`,考点不存在自动建、存在则复用、题干防重 | `.venv/Scripts/python.exe import_questions.py 题库.csv` |
| `generate_explanations.py` | 补解析:基于「题目 + 考点语料」AI 起草 → 审校 → 入库 | `--draft` 生成草稿到 `data/解析草稿.csv`,Excel 审校后 `--apply` 入库 |
| `corpus/import.py` | 写语料:Markdown → `knowledge_points.description`(幂等) | `.venv/Scripts/python.exe corpus/import.py` |

- 录题 CSV 格式:`题目,选项A,选项B,选项C,选项D,选项E,答案,解析,学科,章节,考点,题型,来源,年份`(格式参考 `示例题库.csv`)
- 语料格式:见 `corpus/README.md`——一科一文件,`## 章节:` / `### 考点:` / `**核心讲解**`/`**鉴别要点**`/`**易错点**`/`**记忆口诀**`
- 解析生成分两阶段:草稿落盘 → 人工审校 → 确认入库,不直接写库

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
| POST | /questions/quiz | 组一套题(subject/subjects/chapter/knowledge_point_id/question_ids/count) |
| GET | /questions/subjects | 有题目的科目列表 |
| GET | /questions/{id} | 题目详情(含答案与解析,记录详情用) |
| POST | /questions/answer | 提交答案,返回判分+解析 |
| POST | /sessions/mock/start | 开始模拟:组卷+建会话 |
| POST | /sessions/mock/{id}/progress | 同步模拟进度;status=abandoned 表示放弃 |
| POST | /sessions/mock/{id}/submit | 交卷:判分+落记录+出报告 |
| POST | /sessions/practice | 练习结束,落练习会话(供记录) |
| GET | /sessions?kind=&status=&limit= | 会话历史 / 查未完成模拟 |
| GET | /sessions/{id} | 会话详情(题目+作答+报告) |
| GET | /stats/summary | 今日题数/累计题数/连续打卡 |
| POST | /ai/ask | 针对某题追问答疑(消耗配额) |
| GET | /ai/quota | 今日剩余追问次数 |
| GET | /weakness | 薄弱点清单 |

## 说明

- 启动时自动建表(MVP 阶段);新增 `sessions` 表(练习/模拟会话)由 create_all 自动创建。
- 模拟测试:未作答的题按错误计入,估分才反映真实水平;`paper_type` 只决定目标题量,实际题数与限时按现有题库折算。

## 说明

- 开发期 `user_id` 以 1 占位,登录体系接入后替换。
- 启动时自动建表(MVP 阶段);生产环境迁移到 alembic。
- RAG 检索当前基于考点标签 + 题目上下文;向量检索接口已预留。
