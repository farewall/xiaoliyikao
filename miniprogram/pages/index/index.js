/**首页:渐变 Hero(今日/打卡/AI) + 练习/模拟双入口 + 未完成模拟续考提示*/
const app = getApp()

Page({
  data: {
    todayCount: 0,
    totalCount: 0,
    aiQuota: null,
    greeting: '',
    nickname: ''
  },

  onLoad() {
    // 按时段生成问候语
    const h = new Date().getHours()
    let greeting = '晚上好'
    if (h < 6) greeting = '凌晨好'
    else if (h < 12) greeting = '早上好'
    else if (h < 14) greeting = '中午好'
    else if (h < 18) greeting = '下午好'

    this.setData({
      greeting,
      nickname: (app.globalData.userInfo && app.globalData.userInfo.nickname) || ''
    })
  },

  onShow() {
    // 冷启动时登录可能还没完成,先确保有 token 再发请求
    const ready = wx.getStorageSync('token')
      ? Promise.resolve()
      : app.login()
    ready.then(() => {
      this.loadStats()
      this.loadQuota()
      this.checkResume()
    }).catch(() => {})
  },

  // 今日已刷题数 / 累计已刷题数
  loadStats() {
    app.request({ url: '/stats/summary' })
      .then((res) => this.setData({
        todayCount: res.today_count || 0,
        totalCount: res.total_count || 0
      }))
      .catch(() => {})
  },

  // 今日剩余 AI 追问次数
  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ aiQuota: res.quota_remaining }))
      .catch(() => {})
  },

  // 上次模拟未完成 → 询问是否续考(每次启动只问一次)
  checkResume() {
    if (this._resumeChecked) return
    this._resumeChecked = true
    app.request({ url: '/sessions?kind=mock&status=in_progress&limit=1' })
      .then((list) => {
        if (!list || !list.length) return
        const session = list[0]
        wx.showModal({
          title: '上次模拟未完成',
          content: '还有一套模拟测试没有做完,是否继续?',
          confirmText: '继续考试',
          cancelText: '放弃',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: `/pages/mock/mock?sessionId=${session.id}` })
            } else {
              app.request({
                url: `/sessions/mock/${session.id}/progress`,
                method: 'POST',
                data: { status: 'abandoned' }
              }).catch(() => {})
            }
          }
        })
      })
      .catch(() => {})
  },

  onPractice() {
    wx.navigateTo({ url: '/pages/practice-config/practice-config' })
  },

  onMock() {
    wx.navigateTo({ url: '/pages/mock-config/mock-config' })
  }
})
