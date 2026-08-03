/**我的页:用户卡 + 学习统计(今日/累计题数) + 薄弱点(可点击直达练习) + 历史记录 + AI 配额*/
const app = getApp()

Page({
  data: {
    userInfo: null,
    todayCount: 0,
    totalCount: 0,
    weakPoints: [],
    quota: 0
  },

  onShow() {
    this.setData({ userInfo: app.globalData.userInfo })
    this.loadStats()
    this.loadWeakPoints()
    this.loadQuota()
  },

  loadStats() {
    app.request({ url: '/stats/summary' })
      .then((res) => this.setData({
        todayCount: res.today_count || 0,
        totalCount: res.total_count || 0
      }))
      .catch(() => {})
  },

  loadWeakPoints() {
    app.request({ url: '/weakness' })
      .then((list) => {
        // 薄弱点以「提分空间」姿态呈现:upSpace = 100% - 正确率
        const weakPoints = (list || []).map((item) => ({
          ...item,
          accuracy_percent: Math.round((item.accuracy || 0) * 100),
          upSpace: Math.round((1 - (item.accuracy || 0)) * 100)
        }))
        this.setData({ weakPoints })
      })
      .catch(() => {})
  },

  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ quota: res.quota_remaining }))
      .catch(() => {})
  },

  // 薄弱点 → 直达该考点练习
  onWeakTap(e) {
    const kpId = e.currentTarget.dataset.kpid
    if (!kpId) return
    wx.navigateTo({ url: `/pages/quiz/quiz?knowledge_point_id=${kpId}&count=10` })
  },

  onHistory() {
    wx.navigateTo({ url: '/pages/history/history' })
  },

  onAbout() {
    wx.showModal({
      title: '小鲤医考',
      content: '医学考研(西医综合 306)刷题小程序 v0.1.0。\n陪伴你从医学生到研究生,每一步都算数。',
      showCancel: false,
      confirmText: '知道了'
    })
  }
})
