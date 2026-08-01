/**刷题页:逐题作答,提交后跳解析页*/
const app = getApp()

Page({
  data: {
    loading: true,
    questions: [],
    current: 0,
    selected: [],
    currentQuestion: null,
    optionKeys: []
  },

  onLoad(options) {
    const count = Number(options.count) || 10
    this.loadQuiz(count)
  },

  // 组卷
  loadQuiz(count) {
    this.setData({ loading: true })
    app.request({
      url: '/questions/quiz',
      method: 'POST',
      data: { count }
    })
      .then((questions) => {
        this.setData({ questions, current: 0, loading: false })
        this.prepareQuestion()
      })
      .catch((err) => {
        wx.showToast({ title: err || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  // 准备当前题
  prepareQuestion() {
    const { questions, current } = this.data
    if (!questions.length || current >= questions.length) return
    const q = questions[current]
    this.setData({
      currentQuestion: q,
      optionKeys: Object.keys(q.options),
      selected: []
    })
  },

  // 切换选项(单选直接覆盖,多选可多次点击)
  onToggleOption(e) {
    const key = e.currentTarget.dataset.key
    const { selected, currentQuestion } = this.data
    if (currentQuestion.qtype === 'single') {
      this.setData({ selected: [key] })
    } else {
      const idx = selected.indexOf(key)
      const next = [...selected]
      if (idx > -1) next.splice(idx, 1)
      else next.push(key)
      this.setData({ selected: next })
    }
  },

  // 提交答案
  onSubmit() {
    const { currentQuestion, selected, current, questions } = this.data
    if (!selected.length) {
      wx.showToast({ title: '请先选择答案', icon: 'none' })
      return
    }
    app.request({
      url: '/questions/answer',
      method: 'POST',
      data: {
        question_id: currentQuestion.id,
        user_answer: selected,
        duration_seconds: 0
      }
    })
      .then((result) => {
        // 跳到解析页,带上判分结果
        wx.navigateTo({
          url: `/pages/explain/explain?questionId=${currentQuestion.id}&result=${JSON.stringify(result)}`
        })
      })
      .catch((err) => wx.showToast({ title: err || '提交失败', icon: 'none' }))
  }
})
