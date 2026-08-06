# 数据库设计 — 小鲤医考

> 后端:FastAPI + SQLAlchemy 2.0 / PostgreSQL。
> ORM 模型位于 `backend/app/models/`,本文档为表结构说明。

## 设计理念

围绕「刷题 + AI 答疑 + 薄弱点 + 复习工作台」四条业务线,共 11 张表:

| 表 | 职责 |
|---|---|
| `users` | 用户 |
| `knowledge_points` | 考点(三级结构)——**薄弱点聚合 + RAG 答疑的公共地基** |
| `knowledge_point_relations` | 考点↔考点显式关联边(**关联考点**,举一反三导航用) |
| `question_groups` | 题组(独立题 1:1 / A3/A4 病例 / B 型选项池)——**练习/组卷/展示的单位** |
| `questions` | 题目(子题或独立题,每题一个 `answer` 判分) |
| `question_knowledge_points` | 题目↔考点多对多关联(**附加考点**,RAG 检索广度用) |
| `answer_records` | 答题记录(正确率 / 薄弱点的数据源,**客观性所在地**) |
| `ai_usages` | AI 免费配额(每日追问次数;P1 改按题,见 §8 规划) |
| `sessions` | 练习/模拟会话(题目构成 + 作答结果,支撑中断续考与记录回看) |
| `favorites` | 收藏(题组级,复习引导信号) |
| `wrong_book` | 错题本(题组级,用户工作台:白名单 / 先不练 / 已经会了) |

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

### 3. knowledge_point_relations — 关联考点边表(考点↔考点)

**职责**:承载考点之间的**显式关联边**(如 心律失常 ↔ 洋地黄中毒 ↔ 低钾血症),由语料中每个考点的「关联考点」小节(见 `backend/corpus/README.md`)人工声明、`corpus/import.py` 解析落库。驱动「举一反三」导航——考点详情页展示「相关考点 + 相关练习」。刻意**不是 Graph RAG**(无实体抽取/图遍历):单题讲透场景一次检索够用,手写显式边即把孤立知识点连成网。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `kp_a_id` | FK→knowledge_points 索引 | 边的低 id 端(规范化) |
| `kp_b_id` | FK→knowledge_points 索引 | 边的高 id 端(规范化) |

**唯一约束** `(kp_a_id, kp_b_id)` + **CHECK** `kp_a_id < kp_b_id`。

**约定**:
- **规范化存储**:边是无向的。语料里 A 声明 B、B 也声明 A 时,导入统一归一为 `(min_id, max_id)` 一行,天然去重——人工两侧重复声明不会产生重复边。
- **查询相关考点**:`WHERE kp_a_id = X OR kp_b_id = X`,对称一次取回。
- **相关练习**:考点详情页的「相关练习」= `questions.knowledge_point_id` 落在这些相关考点上(主考点过滤),纯查询,不新增表。
- 与 `question_knowledge_points`(附加考点)的区别:**附加考点是题目↔考点的边(题归因,RAG 广度)**;本表是**考点↔考点的边(知识导航)**。

### 4. question_groups — 题组表(练习/组卷/展示的单位)

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

### 5. questions — 题目表(核心实体)

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

### 6. question_knowledge_points — 附加考点关联表

对应模型:`backend/app/models/question_knowledge_point.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `question_id` | FK→questions 索引 | 题目 |
| `knowledge_point_id` | FK→knowledge_points 索引 | 附加考点 |

**唯一约束** `(question_id, knowledge_point_id)`。

**约定**:`questions.knowledge_point_id` 是**主考点**(薄弱点统计、组卷归属、归因干净);本表只存**附加考点**(一道题跨考的其他考点,RAG 追问时拉取全部关联考点语料),不含主考点。附加考点不进薄弱点/组卷逻辑。

### 7. answer_records — 答题记录表

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

**客观性所在地**:历史对错永不删、考据可查。薄弱点诊断(Wilson 三态)、到期重考排序、错题本白名单推导,全部只认这张表。

### 8. ai_usages — AI 配额表

对应模型:`backend/app/models/quota.py`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | |
| `usage_date` | date | 使用日期 |
| `count` | int 默认 0 | 当日已用追问次数 |
| `created_at` | timestamptz | 服务端默认生成 |

**唯一约束** `(user_id, usage_date)`——一人一天一条计数记录。

> **P1 规划(ADR 0002):改「每日计数」为「按题计数」**——免费层 = 每道题首问免费(子题级,`questions` 一行一次免费首问)。新表 `ai_asks(user_id, question_id, count)` + 唯一约束 `(user_id, question_id)`;订阅开关为配置项,验证期关闭。落地时 `ai_usages` 退役或降级为日志,`services/quota.py` 改造。

### 9. sessions — 会话表(练习 / 模拟测试)

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

### 10. favorites — 收藏表(题组级,复习引导信号)

**职责**:用户主动收藏的题组(五角星),进「我的收藏」页。动机:冲刺期收藏 ≈ 高精度的"未掌握 / 想再看"信号。定位 = **复习引导信号**——收藏题及其考点在收藏页 / 重点回顾 / 自适应抽题中优先出现,影响"练什么";**不进诊断判定**(薄弱点只认 `answer_records` 客观证据)。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | 收藏用户 |
| `group_id` | FK→question_groups 索引 | 收藏题组(整组,含 A3/A4 病例串与 B 型池) |
| `created_at` | timestamptz | 服务端默认生成(「我的收藏」按此排序) |

**唯一约束** `(user_id, group_id)`。

**约定**:
- **单元 = 题组级**:子题无 `scenario` 无法独立渲染,复习单元天然是整组;独立题 1:1 无差别。与「先不练」「已经会了」同为题组级,复习单元全局统一。
- 任何题组都可收藏(不要求答错);模拟考试进行中不可用(考试不打断)。
- 收藏不改变薄弱点诊断;「待评估」考点频繁被收藏时可提示"是否想多练这里"——引导不判定。

### 11. wrong_book — 错题本表(题组级,用户工作台)

**职责**:错题本 = 用户管理的复习工作台,跨练习与模拟聚合。**一行一组,存「在书内」的题组及其用户状态**——答错自动进(白名单),用户可改 先不练(黑名单)/ 已经会了(移出)。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int PK 自增 | |
| `user_id` | FK→users 索引 | |
| `group_id` | FK→question_groups 索引 | 题组(整组) |
| `state` | varchar(16) 默认 `white` | `white`(白名单/待复习) / `park`(先不练/黑名单) / `mastered`(已经会了/移出) |
| `created_at` | timestamptz | 服务端默认生成 |
| `updated_at` | timestamptz | `state` 变更时刷新 |

**唯一约束** `(user_id, group_id)`——一行一组,`state` 三值互斥。

**页面职责拆分**(2026-08-06 定,按「首页=刷题 / 我的=管理与分析」):
- 首页「错题复习」 = `white`:白名单复习队列(到期重考排序、重练)。
- 我的「错题本管理」 = **只放 `park`**:被标记先忽略(先不练)的题,操作 = 移回白名单。
- `mastered`:不占任何列表,只在「我的」统计体现为「已攻克 X 道」正向指标,**不设撤销按钮**——误点后的复活路径 = 再次答错自动回白名单。
- 两处不重叠:一道题任一时刻只在一个地方。

**状态机**:
- **答错自动进**:组内任一子题在 `answer_records` 答错且本表无该组行 → 插入 `state=white`;已有行——`park` 不动(尊重先不练)、`mastered` 改回 `white`(新证据复活)。
- **先不练** → `state=park`(黑名单:暂缓,不催、不进抽题、不进复习队列含到期重考,随时可移回)。
- **移回白名单** → `state=white`(仅 `park` 经「我的错题本管理」的移回操作)。
- **已经会了** → `state=mastered`(移出错题本,错题本越来越少 = 正向反馈)。
- 迁移触发:用户操作(先不练/移回/已经会了)+ 系统「答错自动进」;系统只在答错时动表。

**约定**:
- **白名单 = `state='white'` 的行**:到期重考只作用于它。「我的页」正向指标:剩余数量 = 未 mastered(white + park),「已攻克 X 道」 = `mastered` 计数。
- **客观性住在 `answer_records`**:历史对错永不删、考据可查;本表是工作台视图,「先不练」「已经会了」**都不改变薄弱点诊断**——诊断只认 `answer_records` 客观作答证据,**不读本表**。

## 表关系

```
users ──1:N── answer_records
users ──1:N── sessions
users ──1:N── ai_usages
users ──1:N── favorites
users ──1:N── wrong_book
question_groups ──1:N── questions (group_id)
questions ──1:N── answer_records
knowledge_points ──1:N── questions (knowledge_point_id, 主考点)
questions ──N:M── knowledge_points (question_knowledge_points, 附加考点)
knowledge_points ──N:M── knowledge_points (knowledge_point_relations, 关联考点)
knowledge_points ──self── (parent_id 预留细分)
```

```
              knowledge_points ──N:M── knowledge_points (knowledge_point_relations 关联考点)
                    │ 1
                    │ N(主考点)
                    │
         question_groups ──1:N── questions ──1:N── answer_records ──N:1── users
          (kind/scenario/options)  │ group_id           │              │ 1:N
                                  │                     │ 1:N          ├── sessions(question_ids 软引用 questions)
                                  │                     │              ├── favorites(题组级收藏)
                                  │                     │              └── wrong_book(题组级:白名单/先不练/已经会了)
                                  │
                          question_knowledge_points(附加考点, N:M)
```

## 设计要点

1. **`options` / `answer` 用 JSONB** —— 不锁表结构,单/多选/病例题切换无需改表;将来新增题型同样兼容。
2. **考点三级结构是公共地基** —— 薄弱点分析按 `knowledge_point_id` 聚合错题统计正确率;RAG 答疑按考点检索 `description` 拼上下文。两个核心功能共用一套标签体系。
3. **ai_usages 一人一天一行** —— 结合唯一约束与行锁(`select_for_update`,见 `backend/app/services/quota.py`),免费配额上限锁死,并发请求也刷不破(P1 改按题后同套思路照搬到 `ai_asks`)。
4. **时间戳统一 `server_default=func.now()`** —— 时间由数据库生成,避免应用服务器时钟偏差。
5. **答题记录逐条落库** —— `is_correct` × `knowledge_point_id` 的组合支撑按考点聚合薄弱点。
6. **sessions 只记录"这一轮",答题明细仍归 answer_records** —— 会话表承载一轮作答的题目构成与结果（支撑中断续考、练习/模拟记录回看），薄弱点与每日统计仍由 `answer_records` 聚合，两者各司其职。
7. **主考点 + 附加考点** —— 薄弱点/组卷只看主考点（`questions.knowledge_point_id`，归因干净）；附加考点（`question_knowledge_points`）只喂 RAG 检索广度。题型 `a/b/x` 对齐 306 官方分类（A3/A4 是 A 型子形态，不独立成类型）；判分 `a`/`b` 单选、`x` 多选。
8. **题组是练习/组卷/展示的单位，判分按小题** —— 每题都归组（独立题 1:1，A3/A4 与 B 型 1:N）；共享内容（病例/池）只存题组一行；组内顺序用 `position` 显式保证。前端块状渲染（共享内容一次 + 子题按 position 连续），练习/模拟/记录回看同一套展示；组卷按整块取题、按小题计数、整块必进宁多勿拆。反馈时机仍按模式（练习即时、模拟考完判卷），属模式定义而非展示规则。
9. **收藏 / 错题本两张表,语义不混** —— `favorites`(正向信号,任何题组可收藏)与 `wrong_book`(错题本工作台:答错自动进 + 用户状态)各自独立;两者都**题组级**,与复习单元统一。客观性只住在 `answer_records`——薄弱点诊断只认它,工作台表(`wrong_book` state 迁移)不产生诊断。
10. **关联考点是考点↔考点的边,区别于附加考点(题目↔考点)** —— 边由语料人工声明、导入规范化去重;驱动举一反三导航,不参与薄弱点/组卷。

## 预留能力

- **向量检索(pgvector)**:将来做语义检索 / 相似题推荐时,安装 pgvector 扩展后,在 `questions` 表增加
  `embedding` 向量字段即可(方案见 `backend/app/models/question.py` 注释),当前 MVP 不启用。
- **考点细分**:`knowledge_points.parent_id` 已预留,支持二级考点细化。
- **AI 配额按题**:`ai_asks` 表 + quota 服务改造,见 §8 规划(ADR 0002)。

## 开发约定

- **环境分离**:`xiaoliyikao_dev`(测试)与 `xiaoliyikao_prod`(生产)两个独立数据库,后端通过 `DATABASE_URL` 切换。
- **建表**:MVP 阶段应用启动时 `Base.metadata.create_all()` 自动建表;生产环境切换为 Alembic 迁移。
- **已有表结构变更**:`create_all` 只建新表、不改旧表——列增删/约束变更用幂等迁移脚本(MVP 临时手段,生产切换 Alembic)。已用脚本:新增 `question_knowledge_points` 表;题组迁移(`question_groups` 表 + `questions.group_id/position`、移除 `scenario/series`)见 `backend/migrate_groups.py`。待写脚本:新增 `favorites` / `wrong_book` / `knowledge_point_relations` 三表(建表级,`create_all` 可直接建,无需迁移脚本)。
- **种子数据**:`backend/seed.py` 填充开发用考点与题目,幂等(考点表为空时才会插入)。
