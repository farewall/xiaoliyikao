/**练习页:单科聚焦,答一题判一题,原地反馈 + AI 追问,末题出轻量小结*/
const app = getApp()

Page({
  data: {
    loading: true,
    phase: 'answering',        // answering | summary
    questions: [],
    current: 0,
    currentQuestion: null,
    optionKeys: [],
    selected: [],

    // 原地反馈
    submitted: false,
    lastResult: null,          // {is_correct, correct_answer, explanation}
    userAnswerText: '',
    correctAnswerText: '',

    // AI 追问
    asking: false,
    aiAnswer: '',
    aiReferences: [],
    aiReferencesText: '',
    quotaRemaining: null,
    userQuestion: '',

    // 小结
    correctCount: 0,
    totalCount: 0,
    wrongQuestions: []
  },

  // 本轮配置(送 /sessions/practice 用)
  config: {},
  _answers: [],
  _questionStart: 0,
  _sessionSubmitted: false,

  onLoad(options) {
    this.onLoadQuota()
    if (options.retry) {
      // 重练错题:从存储取上次错题 id
      const ids = wx.getStorageSync('retryIds') || []
      wx.removeStorageSync('retryIds')
      this.config = { count: ids.length }
      this.loadQuizByIds(ids)
      return
    }
    const subject = options.subject ? decodeURIComponent(options.subject) : ''
    const count = Number(options.count) || 10
    const knowledgePointId = Number(options.knowledge_point_id) || 0
    this.config = knowledgePointId
      ? { knowledge_point_id: knowledgePointId, count }
      : { subject, count }
    this.loadQuiz()
  },

  // 组卷(按科目或考点)
  loadQuiz() {
    this.setData({ loading: true })
    app.request({
      url: '/questions/quiz',
      method: 'POST',
      data: this.config
    })
      .then((questions) => {
        if (!questions || !questions.length) {
          wx.showToast({ title: '这个范围还没有题目', icon: 'none' })
          this.setData({ loading: false })
          return
        }
        this._answers = []
        this._sessionSubmitted = false
        this.setData({ questions, current: 0, phase: 'answering', loading: false })
        this.prepareQuestion(0)
      })
      .catch((err) => {
        wx.showToast({ title: err || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  // 重练错题:按指定题 id 组卷
  loadQuizByIds(ids) {
    this.setData({ loading: true })
    app.request({
      url: '/questions/quiz',
      method: 'POST',
      data: { question_ids: ids, count: ids.length }
    })
      .then((questions) => {
        if (!questions || !questions.length) {
          wx.showToast({ title: '没有可重练的错题', icon: 'none' })
          wx.navigateBack()
          return
        }
        this._answers = []
        this._sessionSubmitted = false
        this.setData({ questions, current: 0, phase: 'answering', loading: false })
        this.prepareQuestion(0)
      })
      .catch((err) => {
        wx.showToast({ title: err || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  prepareQuestion(index) {
    const { questions } = this.data
    if (!questions.length || index >= questions.length) return
    const q = questions[index]
    this._questionStart = Date.now()
    this.setData({
      current: index,
      currentQuestion: q,
      optionKeys: Object.keys(q.options),
      selected: [],
      submitted: false,
      lastResult: null,
      aiAnswer: '',
      aiReferences: [],
      aiReferencesText: '',
      userQuestion: ''
    })
  },

  // 单选直接覆盖,多选可多次点击
  onToggleOption(e) {
    if (this.data.submitted) return
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

  onSubmit() {
    const { currentQuestion, selected, submitted } = this.data
    if (submitted) return
    if (!selected.length) {
      wx.showToast({ title: '请先选择答案', icon: 'none' })
      return
    }
    const duration = Math.round((Date.now() - this._questionStart) / 1000)
    app.request({
      url: '/questions/answer',
      method: 'POST',
      data: {
        question_id: currentQuestion.id,
        user_answer: selected,
        duration_seconds: duration
      }
    })
      .then((result) => {
        // 判分来自 /questions/answer(quiz 接口不含 answer,前端无法自行判定)
        this._answers.push({
          question_id: currentQuestion.id,
          user_answer: selected,
          duration_seconds: duration,
          is_correct: !!result.is_correct
        })
        // WXML 不支持方法调用,文本在 JS 层拼好
        this.setData({
          submitted: true,
          lastResult: result,
          userAnswerText: selected.join('、'),
          correctAnswerText: (result.correct_answer || []).join('、')
        })
      })
      .catch((err) => wx.showToast({ title: err || '提交失败', icon: 'none' }))
  },

  // ---- AI 追问(原地展开) ----
  onQuestionInput(e) {
    this.setData({ userQuestion: e.detail.value })
  },

  onAsk() {
    const { userQuestion, currentQuestion, asking } = this.data
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
        question_id: currentQuestion.id,
        user_question: userQuestion,
        user_answer: this.data.selected
      }
    })
      .then((res) => {
        // WXML 不支持方法调用,参考拼接在 JS 层完成
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
  },

  onLoadQuota() {
    app.request({ url: '/ai/quota' })
      .then((res) => this.setData({ quotaRemaining: res.quota_remaining }))
      .catch(() => {})
  },

  // 下一题 / 收尾
  onNext() {
    const { current, questions } = this.data
    if (current + 1 >= questions.length) {
      this.showSummary()
    } else {
      this.prepareQuestion(current + 1)
    }
  },

  // 轻量小结
  showSummary() {
    const { questions } = this.data
    const answers = this._answers
    const correctCount = answers.filter((a) => a.is_correct).length

    const wrongQuestions = []
    for (const a of answers) {
      if (!a.is_correct) {
        const q = questions.find((x) => x.id === a.question_id)
        wrongQuestions.push({ id: a.question_id, stem: q ? q.stem : '', userAnswer: a.user_answer })
      }
    }

    const accuracyPercent = answers.length
      ? Math.round(correctCount / answers.length * 100)
      : 0

    this.setData({
      phase: 'summary',
      correctCount,
      totalCount: answers.length,
      accuracyPercent,
      wrongQuestions
    })

    // 落一条完成的练习会话(供历史记录)
    if (!this._sessionSubmitted && answers.length) {
      this._sessionSubmitted = true
      app.request({
        url: '/sessions/practice',
        method: 'POST',
        data: { config: this.config, answers }
      }).catch(() => {})
    }
  },

  // 从小结进入某道错题的记录详情
  onOpenWrong(e) {
    const { questionid, useranswer } = e.currentTarget.dataset
    if (!questionid) return
    const userAnswer = encodeURIComponent(JSON.stringify(useranswer || []))
    wx.navigateTo({
      url: `/pages/explain/explain?questionId=${questionid}&userAnswer=${userAnswer}&isCorrect=false`
    })
  },

  // 重练错题
  onRetryWrong() {
    const ids = this.data.wrongQuestions.map((w) => w.id)
    if (!ids.length) return
    wx.setStorageSync('retryIds', ids)
    wx.redirectTo({ url: '/pages/quiz/quiz?retry=1' })
  },

  // 再来一组(同范围重新组卷)
  onAgain() {
    const q = this.config.knowledge_point_id
      ? `knowledge_point_id=${this.config.knowledge_point_id}&count=${this.config.count}`
      : `subject=${encodeURIComponent(this.config.subject)}&count=${this.config.count}`
    wx.redirectTo({ url: `/pages/quiz/quiz?${q}` })
  },

  // 完成:回首页
  onFinish() {
    wx.switchTab({ url: '/pages/index/index' })
  }
})
