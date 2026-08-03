/**练习配置页:科目单选 + 题量 → 开始单科练习*/
const app = getApp()

Page({
  data: {
    loading: true,
    subjects: [],
    selectedSubject: '',
    counts: [10, 20, 30],
    selectedCount: 10
  },

  onLoad(options) {
    // 支持 ?subject=X 预选(模拟报告「去练X」按钮直达,用户仍可改选题量)
    const preset = options.subject ? decodeURIComponent(options.subject) : ''
    app.request({ url: '/questions/subjects' })
      .then((subjects) => {
        if (!subjects || !subjects.length) {
          wx.showToast({ title: '题库还空着,请先录入题目', icon: 'none' })
          setTimeout(() => wx.navigateBack(), 1200)
          return
        }
        const selectedSubject = subjects.indexOf(preset) > -1 ? preset : subjects[0]
        this.setData({ subjects, selectedSubject, loading: false })
      })
      .catch(() => {
        wx.showToast({ title: '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  onSelectSubject(e) {
    this.setData({ selectedSubject: e.currentTarget.dataset.subject })
  },

  onSelectCount(e) {
    this.setData({ selectedCount: e.currentTarget.dataset.count })
  },

  onStart() {
    const { selectedSubject, selectedCount } = this.data
    if (!selectedSubject) {
      wx.showToast({ title: '请先选择科目', icon: 'none' })
      return
    }
    const url = `/pages/quiz/quiz?subject=${encodeURIComponent(selectedSubject)}&count=${selectedCount}`
    wx.navigateTo({ url })
  }
})
