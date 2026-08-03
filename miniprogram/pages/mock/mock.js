/**模拟考试页:限时作答,不判分不显示答案,支持中断续考,到时/主动交卷*/
const app = getApp()

Page({
  data: {
    loading: true,
    questions: [],
    current: 0,
    currentQuestion: null,
    optionKeys: [],
    selected: [],
    remaining: 0,
    timeText: '00:00',
    answeredCount: 0,
    totalCount: 0,
    submitting: false
  },

  _sessionId: 0,
  _answerMap: {},      // question_id -> {user_answer, duration_seconds}
  _questionStart: 0,
  _timer: null,
  _syncTick: 0,

  onLoad(options) {
    this._sessionId = Number(options.sessionId) || 0
    if (!this._sessionId) {
      wx.showToast({ title: '会话不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1200)
      return
    }
    this.fetchSession()
  },

  fetchSession() {
    app.request({ url: `/sessions/${this._sessionId}` })
      .then((res) => {
        if (res.status !== 'in_progress') {
          wx.showToast({ title: '该场模拟已结束', icon: 'none' })
          setTimeout(() => wx.navigateBack(), 1200)
          return
        }
        if (!res.questions || !res.questions.length) {
          wx.showToast({ title: '题库为空', icon: 'none' })
          wx.navigateBack()
          return
        }
        // 恢复已作答内容
        const answerMap = {}
        ;(res.answers || []).forEach((a) => {
          answerMap[a.question_id] = {
            user_answer: a.user_answer || [],
            duration_seconds: a.duration_seconds || 0
          }
        })
        this._answerMap = answerMap
        const paperType = (res.config && res.config.paper_type) || 30
        const remaining = res.remaining_seconds != null ? res.remaining_seconds : paperType * 60

        const answeredCount = Object.keys(answerMap).filter((k) => answerMap[k].user_answer.length).length
        this.setData({
          questions: res.questions,
          totalCount: res.questions.length,
          remaining,
          answeredCount,
          loading: false
        })
        this.prepareQuestion(Math.min(res.current_index || 0, res.questions.length - 1))
        this.startTimer()
      })
      .catch((err) => {
        wx.showToast({ title: err || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  prepareQuestion(index) {
    const { questions } = this.data
    if (!questions.length) return
    const q = questions[index]
    const saved = this._answerMap[q.id] || { user_answer: [], duration_seconds: 0 }
    this._questionStart = Date.now()
    this.setData({
      current: index,
      currentQuestion: q,
      optionKeys: Object.keys(q.options),
      selected: saved.user_answer
    })
  },

  // 单选覆盖,多选切换
  onToggleOption(e) {
    const key = e.currentTarget.dataset.key
    const { selected, currentQuestion } = this.data
    let next
    if (currentQuestion.qtype === 'single') {
      next = selected.indexOf(key) > -1 ? [] : [key]
    } else {
      const idx = selected.indexOf(key)
      next = [...selected]
      if (idx > -1) next.splice(idx, 1)
      else next.push(key)
    }
    this._answerMap[currentQuestion.id] = {
      user_answer: next,
      duration_seconds: Math.round((Date.now() - this._questionStart) / 1000)
    }
    const answeredCount = Object.keys(this._answerMap).filter((k) => this._answerMap[k].user_answer.length).length
    this.setData({ selected: next, answeredCount })
  },

  onPrev() {
    if (this.data.current <= 0) return
    this.persistProgress()
    this.prepareQuestion(this.data.current - 1)
  },

  onNext() {
    if (this.data.current >= this.data.questions.length - 1) return
    this.persistProgress()
    this.prepareQuestion(this.data.current + 1)
  },

  // 作答转数组
  answersArray() {
    return Object.keys(this._answerMap).map((qid) => {
      const v = this._answerMap[qid]
      return {
        question_id: Number(qid),
        user_answer: v.user_answer,
        duration_seconds: v.duration_seconds
      }
    })
  },

  // 同步进度到服务端(切题/离开页面/周期)
  persistProgress() {
    const { current, questions } = this.data
    const q = questions[current]
    if (q && this._answerMap[q.id]) {
      this._answerMap[q.id].duration_seconds = Math.round((Date.now() - this._questionStart) / 1000)
    }
    app.request({
      url: `/sessions/mock/${this._sessionId}/progress`,
      method: 'POST',
      data: {
        current_index: current,
        remaining_seconds: this.data.remaining,
        answers: this.answersArray()
      }
    }).catch(() => {})
  },

  // 倒计时
  startTimer() {
    this.updateTimeText()
    this._timer = setInterval(() => {
      const remaining = this.data.remaining - 1
      if (remaining <= 0) {
        clearInterval(this._timer)
        this._timer = null
        this.setData({ remaining: 0, timeText: '00:00' })
        wx.showToast({ title: '时间到,自动交卷', icon: 'none' })
        this.submitFlow()
        return
      }
      this.setData({ remaining, timeText: this.formatTime(remaining) })
      // 每 30 秒同步一次进度
      this._syncTick++
      if (this._syncTick % 30 === 0) this.persistProgress()
    }, 1000)
  },

  formatTime(seconds) {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  },

  updateTimeText() {
    this.setData({ timeText: this.formatTime(this.data.remaining) })
  },

  // 主动交卷
  onSubmit() {
    wx.showModal({
      title: '确认交卷?',
      content: `已作答 ${this.data.answeredCount}/${this.data.totalCount} 题,交卷后不可修改。`,
      confirmText: '交卷',
      cancelText: '继续答题',
      success: (res) => {
        if (res.confirm) this.submitFlow()
      }
    })
  },

  submitFlow() {
    if (this.data.submitting) return
    this.setData({ submitting: true })
    if (this._timer) {
      clearInterval(this._timer)
      this._timer = null
    }
    app.request({
      url: `/sessions/mock/${this._sessionId}/submit`,
      method: 'POST',
      data: {
        remaining_seconds: this.data.remaining,
        answers: this.answersArray()
      }
    })
      .then(() => {
        wx.redirectTo({ url: `/pages/mock-report/mock-report?sessionId=${this._sessionId}` })
      })
      .catch((err) => {
        this.setData({ submitting: false })
        wx.showToast({ title: err || '交卷失败', icon: 'none' })
      })
  },

  onHide() {
    // 离开页面时保存进度(切后台/被杀前的最后一道保险)
    this.persistProgress()
  },

  onUnload() {
    if (this._timer) {
      clearInterval(this._timer)
      this._timer = null
    }
  }
})
