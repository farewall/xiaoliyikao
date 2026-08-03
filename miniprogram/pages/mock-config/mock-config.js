/**模拟测试配置页:科目范围(多选,默认全科) + 卷型 → 开始模拟*/
const app = getApp()

Page({
  data: {
    loading: true,
    subjects: [],
    selectedMap: {},   // subject -> bool
    allSelected: true,
    paperTypes: [30, 60, 180],
    selectedPaper: 30
  },

  onLoad() {
    app.request({ url: '/questions/subjects' })
      .then((subjects) => {
        if (!subjects || !subjects.length) {
          wx.showToast({ title: '题库还空着,请先录入题目', icon: 'none' })
          setTimeout(() => wx.navigateBack(), 1200)
          return
        }
        const selectedMap = {}
        subjects.forEach((s) => { selectedMap[s] = true })
        this.setData({ subjects, selectedMap, allSelected: true, loading: false })
      })
      .catch(() => {
        wx.showToast({ title: '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  toggleAll() {
    const { subjects, allSelected } = this.data
    const selectedMap = {}
    subjects.forEach((s) => { selectedMap[s] = !allSelected })
    this.setData({ selectedMap, allSelected: !allSelected })
  },

  toggleSubject(e) {
    const subject = e.currentTarget.dataset.subject
    const selectedMap = { ...this.data.selectedMap }
    selectedMap[subject] = !selectedMap[subject]
    const allSelected = this.data.subjects.every((s) => selectedMap[s])
    this.setData({ selectedMap, allSelected })
  },

  onSelectPaper(e) {
    this.setData({ selectedPaper: e.currentTarget.dataset.paper })
  },

  onStart() {
    const { selectedMap, allSelected, selectedPaper } = this.data
    const subjects = allSelected
      ? []
      : this.data.subjects.filter((s) => selectedMap[s])
    if (!subjects.length) {
      wx.showToast({ title: '至少选择一个科目', icon: 'none' })
      return
    }
    wx.showLoading({ title: '组卷中…' })
    app.request({
      url: '/sessions/mock/start',
      method: 'POST',
      data: { subjects, paper_type: selectedPaper }
    })
      .then((res) => {
        wx.hideLoading()
        wx.redirectTo({ url: `/pages/mock/mock?sessionId=${res.session_id}` })
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({ title: err || '组卷失败', icon: 'none' })
      })
  }
})
