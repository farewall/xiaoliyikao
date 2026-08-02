# 数据库设计 — 小鲤医考

> 后端:FastAPI + SQLAlchemy 2.0 / PostgreSQL。
> ORM 模型位于 `backend/app/models/`,本文档为表结构说明。

## 设计理念

围绕「刷题 + AI 答疑 + 薄弱点」三条业务线,共 5 张表:

| 表 | 职责 |
|---|---|
| `users` | 用户 |
| `knowledge_points` | 考点(三级结构)——**薄弱点聚合 + RAG 答疑的公共地基** |
| `questions` | 题目 |
| `answer_records` | 答题记录(正确率 / 薄弱点的数据源) |
| `ai_usages` | AI 免费配额(每日追问次数) |

## 表结构

### 1. users — 用户表

对应模型:`backend/app/models/user.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `openid` | varchar(64) **唯一** + 索引 | 微信 openid,用户标识 |
| `nickname` | varchar(64) 可空 | 昵称 |
| `avatar_url` | varchar(512) 可空 | 头像 |
| `created_at` | timestamptz | 服务端默认生成 |
| `updated_at` | timestamptz | 服务端默认生成,更新时自动刷新 |

### 2. knowledge_points — 考点表(三级结构)

对应模型:`backend/app/models/knowledge_point.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `subject` | varchar(64) 索引 | 学科,如"生理学" |
| `chapter` | varchar(64) 索引 | 章节,如"循环系统" |
| `name` | varchar(128) | 考点名,如"房颤" |
| `parent_id` | FK→自身 可空 | 父考点,预留细分 |
| `description` | text 可空 | 考点讲解,**RAG 答疑语料** |
| `created_at` | timestamptz | 服务端默认生成 |

结构:`subject → chapter → name` 三级,与 306 考纲组织方式一致。

### 3. questions — 题目表(核心实体)

对应模型:`backend/app/models/question.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `qtype` | varchar(16) 索引 | 题型:`single` 单选 / `multiple` 多选 / `case` 病例(A3/A4) |
| `stem` | text 非空 | 题干 |
| `options` | **JSONB** | `{"A": "...", "B": "...", ...}` |
| `answer` | **JSONB** | `["A"]` 或 `["A","C"]` |
| `explanation` | text 非空 | AI 基于医学知识自主重写的解析(不录入出版物原文) |
| `knowledge_point_id` | FK→knowledge_points 索引 | 考点归属 |
| `source` | varchar(64) 可空 | 来源,如"真题 2023" |
| `year` | int 可空 | 年份 |
| `created_at` | timestamptz | 服务端默认生成 |

### 4. answer_records — 答题记录表

对应模型:`backend/app/models/answer_record.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | 作答用户 |
| `question_id` | FK→questions 索引 | 作答题目 |
| `user_answer` | JSONB | 用户提交的选项 |
| `is_correct` | boolean | 判分结果 |
| `duration_seconds` | int 可空 | 作答耗时(秒),用于观察卡壳点 |
| `answered_at` | timestamptz 索引 | 作答时间 |

### 5. ai_usages — AI 配额表

对应模型:`backend/app/models/quota.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | |
| `usage_date` | date | 使用日期 |
| `count` | int 默认 0 | 当日已用追问次数 |
| `created_at` | timestamptz | 服务端默认生成 |

**唯一约束** `(user_id, usage_date)`——一人一天一条计数记录。

## 表关系

```
users ──1:N── answer_records
questions ──1:N── answer_records
knowledge_points ──1:N── questions
knowledge_points ──self──(parent_id 预留细分)
users ──1:N── ai_usages
```

```
              knowledge_points
                    │ 1
                    │
              questions (knowledge_point_id)
                    │ 1
                    │
users ──1:N── answer_records ──N:1── questions
users ──1:N── ai_usages
```

## 设计要点

1. **`options` / `answer` 用 JSONB** —— 不锁表结构,单/多选/病例题切换无需改表;将来新增题型同样兼容。
2. **考点三级结构是公共地基** —— 薄弱点分析按 `knowledge_point_id` 聚合错题统计正确率;RAG 答疑按考点检索 `description` 拼上下文。两个核心功能共用一套标签体系。
3. **ai_usages 一人一天一行** —— 结合唯一约束与行锁(`select_for_update`,见 `backend/app/services/quota.py`),免费配额上限锁死,并发请求也刷不破。
4. **时间戳统一 `server_default=func.now()`** —— 时间由数据库生成,避免应用服务器时钟偏差。
5. **答题记录逐条落库** —— `is_correct` × `knowledge_point_id` 的组合支撑按考点聚合薄弱点。

## 预留能力

- **向量检索(pgvector)**:将来做语义检索 / 相似题推荐时,安装 pgvector 扩展后,在 `questions` 表增加
  `embedding` 向量字段即可(方案见 `backend/app/models/question.py` 注释),当前 MVP 不启用。
- **考点细分**:`knowledge_points.parent_id` 已预留,支持二级考点细化。

## 开发约定

- **环境分离**:`xiaoliyikao_dev`(测试)与 `xiaoliyikao_prod`(生产)两个独立数据库,后端通过 `DATABASE_URL` 切换。
- **建表**:MVP 阶段应用启动时 `Base.metadata.create_all()` 自动建表;生产环境切换为 Alembic 迁移。
- **种子数据**:`backend/seed.py` 填充开发用考点与题目,幂等(考点表为空时才会插入)。
