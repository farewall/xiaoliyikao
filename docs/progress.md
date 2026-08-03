# 项目进度与待办

> 更新时间:2026-08-03
> 文档:数据库设计见 `docs/database-design.md`,产品讨论见 `讨论记录.md`

## 一、当前进度

### ✅ 已完成

1. **后端本地跑通,全链路验证通过**
   - 本机 venv 装好后端依赖(FastAPI / SQLAlchemy / psycopg2 / pyjwt)
   - 后端连接服务器 dev 库,`/health`、登录、配额、组卷、判分、薄弱点 6 项接口全部验证通过
   - 删除 Docker(Dockerfile / docker-compose.yml),改为裸跑 uvicorn

2. **数据库环境**
   - 服务器建 PostgreSQL 双库:`xiaoliyikao_dev`(测试) / `xiaoliyikao_prod`(生产),用户 `xiaoliyikao`
   - 5 张表自动创建:users / knowledge_points / questions / answer_records / ai_usages
   - 种子数据:`backend/seed.py`(6 考点 + 10 题,幂等可重复执行)
   - `.gitignore` 保护 `.env` 并从 git 移除,防止密码/密钥入库

3. **Bug 修复(4 个)**
   - AI 配额硬编码 `user_id=1` 触发外键约束
   - 占位用户插入后自增序列未同步,登录主键冲突
   - `profile.wxml` 模板内调用 `.toFixed()`(WXML 不支持方法调用)
   - 前端登录 `success` 回调为死代码,userInfo 始终为空

4. **Token 认证体系完成**
   - 新增 `services/auth.py`:JWT 签发 + `get_current_user` 依赖
   - 登录返回 `{token, user}`,三处 `DEV_USER_ID` 全部替换为真实用户
   - 前端 `app.js`:存 token、请求带 `Authorization`、401 自动重登
   - 验证:无 token → 401 / 有效 token → 通过 / 错误 token → 401

5. **文档**:`docs/database-design.md` 数据库设计

6. **V1 交互重构完成**(练习 + 模拟测试双模式,ADR 0001 + CONTEXT.md 术语表)
   - 后端:新增 `sessions` 表 + 8 个新/改接口(组卷按范围、`GET /questions/{id}`、`/sessions` 系列、`/stats/summary`),代码完成
   - 前端:首页状态条+双入口、练习配置页、练习原地反馈+轻量小结、模拟配置/考试/报告页、记录详情页、我的页统计+薄弱点可点+历史记录页
   - ✅ 后端已全链路验证(本会话):14 个接口冒烟测试全 PASS,连接阿里云 dev 库自动建表
   - ⚠️ 前端改版未在微信开发者工具验证(需装工具后联调,重点:历史页分组/报告「去练X」)

7. **前端「清新医药风」全站改版完成**(grill-with-docs 讨论产出;设计原则见 CONTEXT.md「核心原则」)
   - 全局设计系统:app.wxss 统一 `.option/.chip/.btn-secondary/.section-title/AI 追问块` 等共享类(路线 A,不抽组件)
   - 首页:撤掉次级入口行,回归「Hero + 练习/模拟双入口」(首页职责 = 开练)
   - 我的页:重组为「数据区(统计/提分点/历史)+ 设置区(AI 配额/关于)」
   - 报告页:最低分科目改「提分空间」措辞 +「去练X」按钮直达预选科目配置页(用户仍有选题量权力)
   - quiz/explain:判分颜色清晰 + 措辞正向化(「这题值得回看」/「重点回顾」/「答对了 N 题」)
   - 历史页:按时间分组(今天/昨天/近7天/更早)+ 类型图标
   - 全站文案遵循「陪伴式语气 + 诚实不回避」两大核心原则

8. **内容生产工具链完成**(录题 → 补解析 → 写语料,详见 `backend/README.md`)
   - `import_questions.py`:CSV 批量录题,考点自动建/复用/题干防重
   - `generate_explanations.py`:基于「题目+语料」AI 起草解析 → 审校 → 入库(两阶段)
   - `corpus/import.py` + `corpus/*.md`:考点语料库(Markdown 源 → knowledge_points.description,幂等)
   - RAG 升级:用户所选答案进上下文 + 结构化多段检索(同章节兄弟考点)
   - 示例:`backend/示例题库.csv`(录题格式参考)

---

## 二、待办事项

### P0 — 上线前必做

- [ ] 安装微信开发者工具,完成小程序前端联调(登录/刷题/解析/我的)
- [ ] 填 `DEEPSEEK_API_KEY` 到 `.env`(否则 `/ai/ask` 一直 503)
- [ ] **ICP 备案通过**(个人备案,1~2 周)
- [ ] 服务器部署:装 Python 3.12 → 传代码 → venv 装依赖 → uvicorn + **systemd 守护**
- [ ] HTTPS + Nginx 反向代理(备案通过后)
- [ ] 注册小程序,拿真实 `WECHAT_APPID`/`WECHAT_SECRET` 填入 `.env`
- [ ] **小程序注册主体策略**(注册前定):验证期只用免费个人主体 / 开发者工具测试号,**只给测试用、不积累真实用户**。⚠️ 红线:换 AppID 前别积累真实用户(openid 按 AppID 隔离,换号=历史数据对不上人);将来要收费 → 有真用户时走官方「主体迁移」保留 AppID,而非注册新号重发。收费路径:个体户 2026 可开虚拟支付(审核严),个人主体不可开
- [ ] `JWT_SECRET` 换成强随机串(现为开发默认值)
- [ ] **安全加固**:关闭服务器 5432 公网暴露;数据库弱密码 `shterm123` 改强

### P1 — 上线后 / 产品迭代

- [ ] **RAG 向量升级**(方案已定):
      `document_chunks` 独立表 + pgvector(HNSW) + 阿里云 DashScope `text-embedding-v3`
      → 建索引脚本 → 改造 `rag.py` 的 `_retrieve`(向量召回 + 强制带当前题)
- [ ] 小程序备案(上线前)
- [ ] 生产环境切换 Alembic 迁移(替代启动自动建表)
- [ ] 题库数据正式录入 / 导入
- [ ] **薄弱点诊断升级**(grill-with-docs 讨论产出):
      三态诊断——确认弱 / **待评估**(样本不足,不判弱也不判强) / 确认不弱
      → 排序改用带样本量加权的置信度(Wilson 下界),不用裸正确率
      → 薄弱点页 UI 展示「待评估」考点,数据不足绝不贴「弱」标签
- [ ] **AI 追问配额改「按题计数」**(见 ADR 0002):
      后端从「每日计数」改为「按题计数」(`ai_asks` 表:user_id + question_id + 次数)
      → 免费层 = 每道题首问免费(不管对错);订阅开关为配置项,验证期关闭
- [ ] **AI 订阅支付专项**(见 ADR 0002,产品价值验证后再立项):
      核实小程序虚拟支付当前政策 / 所需类目资质 + H5/公众号绕行备选方案

### P2 — 远期 / 需专门立项

- [ ] **自适应抽题**(grill-with-docs 讨论产出):抽题从纯随机改为「优先采样样本不足 / 高不确定考点」的题目,加速薄弱点诊断收敛

---

## 三、关键环境信息

> ⚠️ 密码/密钥只在 `.env`(已 gitignore),不写进任何提交文件。

| 项 | 值 |
|---|---|
| 服务器 | `120.26.77.248`(阿里云轻量,华东1杭州,2C2G/40G,Ubuntu 24.04) |
| 数据库 | PostgreSQL 16,用户 `xiaoliyikao`,库 `xiaoliyikao_dev` / `xiaoliyikao_prod` |
| 后端启动(本地联调) | `cd backend` + 覆盖 `DATABASE_URL` 为服务器 IP + `uvicorn app.main:app` |
| 备案信息 | 个人备案,网站名称用「小鲤随笔」(中性合规),备案地区按身份证地址所在省 |
