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

### 🔄 进行中

- **ICP 备案**:个人备案,网站名称需合规(不能用「小鲤医考」,改用中性名如「小鲤随笔」)
- **前端联调**:微信开发者工具尚未安装

---

## 二、待办事项

### P0 — 上线前必做

- [ ] 安装微信开发者工具,完成小程序前端联调(登录/刷题/解析/我的)
- [ ] 填 `DEEPSEEK_API_KEY` 到 `.env`(否则 `/ai/ask` 一直 503)
- [ ] **ICP 备案通过**(个人备案,1~2 周)
- [ ] 服务器部署:装 Python 3.12 → 传代码 → venv 装依赖 → uvicorn + **systemd 守护**
- [ ] HTTPS + Nginx 反向代理(备案通过后)
- [ ] 注册小程序,拿真实 `WECHAT_APPID`/`WECHAT_SECRET` 填入 `.env`
- [ ] `JWT_SECRET` 换成强随机串(现为开发默认值)
- [ ] **安全加固**:关闭服务器 5432 公网暴露;数据库弱密码 `shterm123` 改强

### P1 — 上线后 / 产品迭代

- [ ] **RAG 向量升级**(方案已定):
      `document_chunks` 独立表 + pgvector(HNSW) + 阿里云 DashScope `text-embedding-v3`
      → 建索引脚本 → 改造 `rag.py` 的 `_retrieve`(向量召回 + 强制带当前题)
- [ ] 小程序备案(上线前)
- [ ] 生产环境切换 Alembic 迁移(替代启动自动建表)
- [ ] 题库数据正式录入 / 导入

---

## 三、关键环境信息

> ⚠️ 密码/密钥只在 `.env`(已 gitignore),不写进任何提交文件。

| 项 | 值 |
|---|---|
| 服务器 | `120.26.77.248`(阿里云轻量,华东1杭州,2C2G/40G,Ubuntu 24.04) |
| 数据库 | PostgreSQL 16,用户 `xiaoliyikao`,库 `xiaoliyikao_dev` / `xiaoliyikao_prod` |
| 后端启动(本地联调) | `cd backend` + 覆盖 `DATABASE_URL` 为服务器 IP + `uvicorn app.main:app` |
| 备案信息 | 个人备案,网站名称用「小鲤随笔」(中性合规),备案地区按身份证地址所在省 |
