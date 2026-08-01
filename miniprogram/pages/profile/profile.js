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
      .then((list) => this.setData({ weakPoints: list }))
      .catch(() => {})
  },

  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ quota: res.quota_remaining }))
      .catch(() => {})
  }
})
