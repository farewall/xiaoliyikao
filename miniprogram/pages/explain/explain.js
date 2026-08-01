/**解析与答疑页:展示判分/解析,支持对本题追问 AI*/

const app = getApp()

Page({
  data: {
    questionId: null,
    result: null,      // 判分结果(含解析)
    question: null,    // 题目详情(题干/选项)
    optionKeys: [],
    isCorrect: false,
    userQuestion: '',
    asking: false,
    aiAnswer: '',
    aiReferences: [],
    quotaRemaining: null
  },

  onLoad(options) {
    const questionId = Number(options.questionId)
    let result = null
    try {
      result = JSON.parse(decodeURIComponent(options.result || '{}'))
    } catch (e) {
      result = {}
    }
    this.setData({
      questionId,
      result,
      isCorrect: !!result.is_correct
    })
    this.loadQuestion(questionId)
    this.loadQuota()
  },

  // 加载题目详情(题干/选项)
  loadQuestion(id) {
    // MVP:题目详情通过 quiz 接口只取到题干,这里暂以判分结果兜底
    // 完整做法:后端加 GET /questions/{id},返回题干+选项
  },

  loadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ quotaRemaining: res.quota_remaining }))
      .catch(() => {})
  },

  onQuestionInput(e) {
    this.setData({ userQuestion: e.detail.value })
  },

  // 追问 AI
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
        user_question: userQuestion
      }
    })
      .then((res) => {
        this.setData({
          aiAnswer: res.answer,
          aiReferences: res.references || [],
          quotaRemaining: res.quota_remaining,
          asking: false
        })
      })
      .catch((err) => {
        wx.showToast({ title: err || '追问失败', icon: 'none' })
        this.setData({ asking: false })
      })
  },

  // 下一题(返回刷题页)
  onNext() {
    wx.navigateBack()
  }
})
