# 数据库设计 — 小鲤医考

> 后端:FastAPI + SQLAlchemy 2.0 / PostgreSQL。
> ORM 模型位于 `backend/app/models/`,本文档为表结构说明。

## 设计理念

围绕「刷题 + AI 答疑 + 薄弱点」三条业务线,共 8 张表:

| 表 | 职责 |
|---|---|
| `users` | 用户 |
| `knowledge_points` | 考点(三级结构)——**薄弱点聚合 + RAG 答疑的公共地基** |
| `question_groups` | 题组(独立题 1:1 / A3/A4 病例 / B 型选项池)——**练习/组卷/展示的单位** |
| `questions` | 题目(子题或独立题,每题一个 `answer` 判分) |
| `question_knowledge_points` | 题目↔考点多对多关联(**附加考点**,RAG 检索广度用) |
| `answer_records` | 答题记录(正确率 / 薄弱点的数据源) |
| `ai_usages` | AI 免费配额(每日追问次数) |
| `sessions` | 练习/模拟会话(题目构成 + 作答结果,支撑中断续考与记录回看) |

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

### 3. question_groups — 题组表(练习/组卷/展示的单位)

对应模型:`backend/app/models/question_group.py`

**职责**:承载一块题的**共享内容**与**组内顺序**,是练习、组卷、前端展示的单位。判分与薄弱点不经过它(按小题见 `questions`)。

三种 `kind`:

| kind | 含义 | 共享内容 | 子题特点 |
|---|---|---|---|
| `single` | 独立题(单选/多选),与题目 1:1 | 无 | 题目自含完整题干与选项 |
| `case` | A3/A4 共享病例 | `scenario`(病例文本) | 子题 `stem` 存纯问句、各自有 `options` |
| `pool` | B 型共用选项池 | `options`(池) | 子题 `stem` 存问句、`options` 为空(渲染取池) |

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `kind` | varchar(16) 索引 | `single` / `case` / `pool` |
| `scenario` | text 可空 | A3/A4 共享病例(仅 `case`) |
| `options` | JSONB 可空 | B 型共用选项池(仅 `pool`) |
| `created_at` | timestamptz | 服务端默认生成 |

**共享内容只存题组一行**——改病例/改池 = 改一处,块内永不失一致(取代早期「每子题重复存 scenario/options」的方案,见 ADR 0004)。

### 4. questions — 题目表(核心实体)

对应模型:`backend/app/models/question.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `group_id` | FK→question_groups **非空** + 索引 | 所属题组;独立题组 1:1,病例/池子题共用一组 |
| `position` | int **非空** | 组内顺序(1,2,3…),显式排序 |
| `qtype` | varchar(16) 索引 | 题型:`a` A型单选(含A1/A2/A3/A4) / `b` B型配伍(共用选项池) / `x` X型多选 |
| `stem` | text 非空 | 题干(子题时为纯问句) |
| `options` | JSONB **可空** | `{"A": "...", "B": "...", ...}`;A1/A2/X 独立题、A3/A4 子题有;B 型子题为空(取组的池) |
| `answer` | JSONB 非空 | `["A"]` 或 `["A","C"]` |
| `explanation` | text 非空 | AI 基于医学知识自主重写的解析(不录入出版物原文) |
| `knowledge_point_id` | FK→knowledge_points 索引 | **主考点**(薄弱点/组卷归因);附加考点见 `question_knowledge_points` |
| `source` | varchar(64) 可空 | 来源,如"真题 2023" |
| `year` | int 可空 | 年份 |
| `created_at` | timestamptz | 服务端默认生成 |

**约定**:
- **判分、薄弱点、错题全部按「小题」**:每个子题独立判分(`answer`)、独立归主考点(`knowledge_point_id`),`answer_records` 一行一题。题组只负责抽取/展示/顺序,不参与判分。
- **组内顺序用 `position` 显式保证**(不用 id 递增):子题删除后重插会拿新 id,若按 id 排序会把 A3/A4 的临床顺序(诊断→检查→治疗)打乱。
- **组卷按整块取题**:抽到题组内任一子题即拉整个题组,组内按 `position` 排序;计数按小题,到目标可略超(**整块必进,宁多勿拆**,不拆散病例/池)。
- 练习/模拟的 `sessions.question_ids` 仍是小题 id 列表(出场顺序快照),不存题组 id——回看的是定格时的题目构成,内容后续改动不影响历史记录。

### 5. question_knowledge_points — 附加考点关联表

对应模型:`backend/app/models/question_knowledge_point.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `question_id` | FK→questions 索引 | 题目 |
| `knowledge_point_id` | FK→knowledge_points 索引 | 附加考点 |

**唯一约束** `(question_id, knowledge_point_id)`。

**约定**:`questions.knowledge_point_id` 是**主考点**(薄弱点统计、组卷归属、归因干净);本表只存**附加考点**(一道题跨考的其他考点,RAG 追问时拉取全部关联考点语料),不含主考点。附加考点不进薄弱点/组卷逻辑。

### 6. answer_records — 答题记录表

对应模型:`backend/app/models/answer_record.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | 作答用户 |
| `question_id` | FK→questions 索引 | 作答题目(小题) |
| `user_answer` | JSONB | 用户提交的选项 |
| `is_correct` | boolean | 判分结果 |
| `duration_seconds` | int 可空 | 作答耗时(秒),用于观察卡壳点 |
| `answered_at` | timestamptz 索引 | 作答时间 |

### 7. ai_usages — AI 配额表

对应模型:`backend/app/models/quota.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | |
| `usage_date` | date | 使用日期 |
| `count` | int 默认 0 | 当日已用追问次数 |
| `created_at` | timestamptz | 服务端默认生成 |

**唯一约束** `(user_id, usage_date)`——一人一天一条计数记录。

### 8. sessions — 会话表(练习 / 模拟测试)

对应模型:`backend/app/models/session.py`

统一承载两类"一轮作答":
- `kind=practice`:练习会话,结束时一次性落库,供「练习记录 / 该轮错题回顾」
- `kind=mock`:模拟测试会话,考试中持续更新进度(题目/答案/剩余时间),支撑「中断续考」;交卷时判分出报告

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | 会话归属用户 |
| `kind` | varchar(16) | `practice` / `mock` |
| `status` | varchar(16) | `in_progress` / `completed` / `abandoned` |
| `config` | JSONB | 组卷配置:`{subject/subjects, count/paper_type, knowledge_point_id?}` |
| `question_ids` | JSONB | 题目(小题)id 列表(按出场顺序) |
| `answers` | JSONB | 作答明细:`[{question_id, user_answer, duration_seconds, is_correct}]` |
| `current_index` | int 默认 0 | 进行中位置(模拟续考用) |
| `remaining_seconds` | int 可空 | 剩余时间(秒),仅 mock |
| `report` | JSONB 可空 | mock 交卷后的报告(成绩/估分/各科正确率) |
| `started_at` | timestamptz | 服务端默认生成 |
| `finished_at` | timestamptz 可空 | 完成/放弃时间 |

## 表关系

```
users ──1:N── answer_records
users ──1:N── sessions
users ──1:N── ai_usages
question_groups ──1:N── questions (group_id)
questions ──1:N── answer_records
knowledge_points ──1:N── questions (knowledge_point_id, 主考点)
questions ──N:M── knowledge_points (question_knowledge_points, 附加考点)
knowledge_points ──self── (parent_id 预留细分)
```

```
              knowledge_points
                    │ 1
                    │ N(主考点)
                    │
         question_groups ──1:N── questions ──1:N── answer_records ──N:1── users
          (kind/scenario/options)  │ group_id           │
                                  │                     │ 1:N
                                  │                sessions(question_ids 软引用 questions)
                                  │
                          question_knowledge_points(附加考点, N:M)
```

## 设计要点

1. **`options` / `answer` 用 JSONB** —— 不锁表结构,单/多选/病例题切换无需改表;将来新增题型同样兼容。
2. **考点三级结构是公共地基** —— 薄弱点分析按 `knowledge_point_id` 聚合错题统计正确率;RAG 答疑按考点检索 `description` 拼上下文。两个核心功能共用一套标签体系。
3. **ai_usages 一人一天一行** —— 结合唯一约束与行锁(`select_for_update`,见 `backend/app/services/quota.py`),免费配额上限锁死,并发请求也刷不破。
4. **时间戳统一 `server_default=func.now()`** —— 时间由数据库生成,避免应用服务器时钟偏差。
5. **答题记录逐条落库** —— `is_correct` × `knowledge_point_id` 的组合支撑按考点聚合薄弱点。
6. **sessions 只记录"这一轮",答题明细仍归 answer_records** —— 会话表承载一轮作答的题目构成与结果（支撑中断续考、练习/模拟记录回看），薄弱点与每日统计仍由 `answer_records` 聚合，两者各司其职。
7. **主考点 + 附加考点** —— 薄弱点/组卷只看主考点（`questions.knowledge_point_id`，归因干净）；附加考点（`question_knowledge_points`）只喂 RAG 检索广度。题型 `a/b/x` 对齐 306 官方分类（A3/A4 是 A 型子形态，不独立成类型）；判分 `a`/`b` 单选、`x` 多选。
8. **题组是练习/组卷/展示的单位，判分按小题** —— 每题都归组（独立题 1:1，A3/A4 与 B 型 1:N）；共享内容（病例/池）只存题组一行；组内顺序用 `position` 显式保证。前端块状渲染（共享内容一次 + 子题按 position 连续），练习/模拟/记录回看同一套展示；组卷按整块取题、按小题计数、整块必进宁多勿拆。反馈时机仍按模式（练习即时、模拟考完判卷），属模式定义而非展示规则。

## 预留能力

- **向量检索(pgvector)**:将来做语义检索 / 相似题推荐时,安装 pgvector 扩展后,在 `questions` 表增加
  `embedding` 向量字段即可(方案见 `backend/app/models/question.py` 注释),当前 MVP 不启用。
- **考点细分**:`knowledge_points.parent_id` 已预留,支持二级考点细化。

## 开发约定

- **环境分离**:`xiaoliyikao_dev`(测试)与 `xiaoliyikao_prod`(生产)两个独立数据库,后端通过 `DATABASE_URL` 切换。
- **建表**:MVP 阶段应用启动时 `Base.metadata.create_all()` 自动建表;生产环境切换为 Alembic 迁移。
- **已有表结构变更**:`create_all` 只建新表、不改旧表——列增删/约束变更用幂等迁移脚本(MVP 临时手段,生产切换 Alembic)。已用脚本:新增 `question_knowledge_points` 表;题组迁移(`question_groups` 表 + `questions.group_id/position`、移除 `scenario/series`)见 `backend/migrate_groups.py`。
- **种子数据**:`backend/seed.py` 填充开发用考点与题目,幂等(考点表为空时才会插入)。
