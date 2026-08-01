# 小程序前端

原生微信小程序。刷题 + AI 答疑 + 薄弱点。

## 运行

1. 打开 **微信开发者工具**。
2. 选择「导入项目」→ 目录选 `miniprogram/`。
3. AppID:使用「测试号」即可(`project.config.json` 里已设 `touristappid`)。
4. 确保后端已启动(见 `../backend/README.md`),地址默认为 `http://localhost:8000`。
5. **开发期需勾选「不校验合法域名、web-view(业务域名)、TLS 版本以及 HTTPS 证书」**,否则无法访问本地后端。

## 页面

| 页面 | 说明 |
|---|---|
| `pages/index/index` | 首页:刷题入口 + AI 配额 |
| `pages/quiz/quiz` | 刷题:逐题作答 |
| `pages/explain/explain` | 解析 + AI 追问答疑 |
| `pages/profile/profile` | 我的:薄弱点 + 配额 |

## 请求封装

所有请求走 `app.js` 里的 `app.request()`:
- 自动拼接 `baseUrl`(`globalData.baseUrl`,默认 `http://localhost:8000`)。
- 统一错误处理:后端 `detail` 字段透传给 UI。
- 登录:`onLaunch` 时自动 `wx.login` → `/users/login`。

部署时把 `globalData.baseUrl` 改为你的备案域名即可。
