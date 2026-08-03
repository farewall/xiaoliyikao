/**记录详情页:展示题目 + 你的答案 + 正确答案 + 解析 + AI 追问
(从练习小结错题 / 模拟报告错题 / 历史记录进入,不再承担练习主流程)*/
const app = getApp()

Page({
  data: {
    loading: true,
    questionId: null,
    question: null,       // {stem, options, answer, explanation}
    optionStates: [],     // [{key, text, state}]
    isCorrect: false,
    answerText: '',
    userAnswerText: '',

    asking: false,
    aiAnswer: '',
    aiReferences: [],
    aiReferencesText: '',
    quotaRemaining: null,
    userQuestion: ''
  },

  onLoad(options) {
    const questionId = Number(options.questionId)
    let userAnswer = []
    try {
      userAnswer = JSON.parse(decodeURIComponent(options.userAnswer || '[]')) || []
    } catch (e) {
      userAnswer = []
    }
    const isCorrect = options.isCorrect === 'true'
    this._userAnswer = userAnswer
    this.setData({
      questionId,
      isCorrect,
      userAnswerText: userAnswer.join('、')
    })
    this.loadQuestion(questionId)
    this.loadQuota()
  },

  // 真正加载题目详情(题干/选项/答案/解析)
  loadQuestion(id) {
    app.request({ url: `/questions/${id}` })
      .then((q) => {
        const optionStates = Object.keys(q.options || {}).map((key) => {
          let state = ''
          const inCorrect = (q.answer || []).indexOf(key) > -1
          const inUser = (this._userAnswer || []).indexOf(key) > -1
          if (inCorrect) state = 'correct'
          if (inUser && !inCorrect) state = 'user'
          return { key, text: q.options[key], state }
        })
        this.setData({
          loading: false,
          question: q,
          optionStates,
          answerText: (q.answer || []).join('、')
        })
      })
      .catch((err) => {
        wx.showToast({ title: err || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ quotaRemaining: res.quota_remaining }))
      .catch(() => {})
  },

  onQuestionInput(e) {
    this.setData({ userQuestion: e.detail.value })
  },

  onAsk() {
    const { userQuestion, questionId, asking } = this.data
    if (asking) return
    if (!userQuestion.trim()) {
      wx.showToast({ title: '先输入你的问题', icon: 'none' })
      return
    }
    this.setData({ asking: true })
    app.request({
      url: '/ai/ask',
      method: 'POST',
      data: {
        question_id: questionId,
        user_question: userQuestion,
        user_answer: this._userAnswer || []
      }
    })
      .then((res) => {
        this.setData({
          aiAnswer: res.answer,
          aiReferences: res.references || [],
          aiReferencesText: (res.references || []).join(' · '),
          quotaRemaining: res.quota_remaining,
          asking: false
        })
      })
      .catch((err) => {
        wx.showToast({ title: err || '追问失败', icon: 'none' })
        this.setData({ asking: false })
      })
  }
})
