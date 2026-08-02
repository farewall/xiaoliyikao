/**我的页:用户信息 + 薄弱点 + 配额*/
const app = getApp()

Page({
  data: {
    userInfo: null,
    weakPoints: [],
    quota: 0
  },

  onShow() {
    this.setData({ userInfo: app.globalData.userInfo })
    this.loadWeakPoints()
    this.loadQuota()
  },

  loadWeakPoints() {
    app.request({ url: '/weakness' })
      .then((list) => {
        // WXML 模板不支持调用方法(如 .toFixed),百分比在 JS 层算好再展示
        const weakPoints = (list || []).map((item) => ({
          ...item,
          accuracy_percent: Math.round((item.accuracy || 0) * 100)
        }))
        this.setData({ weakPoints })
      })
      .catch(() => {})
  },

  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ quota: res.quota_remaining }))
      .catch(() => {})
  }
})
