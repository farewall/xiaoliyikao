/**首页:刷题入口 + AI 配额展示*/
const app = getApp()

Page({
  data: {
    quota: 0,
    quotaLoaded: false
  },

  onShow() {
    this.loadQuota()
  },

  // 加载今日剩余 AI 追问次数
  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => {
        this.setData({ quota: res.quota_remaining, quotaLoaded: true })
      })
      .catch(() => {
        this.setData({ quotaLoaded: false })
      })
  },

  // 开始刷题
  onQuiz(e) {
    const count = e.currentTarget.dataset.count
    wx.navigateTo({
      url: `/pages/quiz/quiz?count=${count}`
    })
  }
})
