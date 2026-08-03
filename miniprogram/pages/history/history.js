/**历史记录页:练习(可展开该轮错题) / 模拟(重看报告),按时间分组(今天/昨天/近7天/更早)*/
const app = getApp()

const pad = (n) => String(n).padStart(2, '0')

Page({
  data: {
    tab: 'practice',           // practice | mock
    practiceGroups: [],        // [{label, items: []}]
    mockGroups: [],
    loadingPractice: true,
    loadingMock: true
  },

  onLoad() {
    this.loadPractice()
    this.loadMock()
  },

  loadPractice() {
    app.request({ url: '/sessions?kind=practice&limit=50' })
      .then((list) => {
        const items = (list || []).map((s) => {
          const total = s.total_count || 0
          const config = s.config || {}
          return {
            id: s.id,
            _time: s.started_at,
            timeLabel: this.timeText(s.started_at),
            title: config.subject ? `${config.subject} 练习` : '考点练习',
            count: config.count || total,
            correct: s.correct_count,
            total,
            accuracyPercent: total ? Math.round(s.correct_count / total * 100) : 0,
            expanded: false,
            wrongQuestions: []
          }
        })
        this.setData({ practiceGroups: this.groupByDate(items), loadingPractice: false })
      })
      .catch(() => this.setData({ loadingPractice: false }))
  },

  loadMock() {
    app.request({ url: '/sessions?kind=mock&limit=50' })
      .then((list) => {
        const items = (list || []).map((s) => {
          const total = s.total_count || 0
          const config = s.config || {}
          const report = s.report || {}
          return {
            id: s.id,
            _time: s.started_at,
            timeLabel: this.timeText(s.started_at),
            paperType: config.paper_type || total,
            correct: s.correct_count,
            total,
            accuracyPercent: total ? Math.round(s.correct_count / total * 100) : 0,
            estScore: report.est_score
          }
        })
        this.setData({ mockGroups: this.groupByDate(items), loadingMock: false })
      })
      .catch(() => this.setData({ loadingMock: false }))
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab })
  },

  // 按时间分组:今天 / 昨天 / M月D日(近一周) / 更早
  groupByDate(items) {
    const order = []
    const map = {}
    for (const it of items) {
      const label = this.dateBucket(it._time)
      if (!map[label]) { map[label] = []; order.push(label) }
      map[label].push(it)
    }
    return order.map((label) => ({ label, items: map[label] }))
  },

  dateBucket(time) {
    if (!time) return '更早'
    const d = new Date(time)
    if (isNaN(d.getTime())) return '更早'
    const now = new Date()
    const start = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime()
    const diff = Math.round((start(now) - start(d)) / 86400000)
    if (diff <= 0) return '今天'
    if (diff === 1) return '昨天'
    if (diff <= 6) return `${d.getMonth() + 1}月${d.getDate()}日`
    return '更早'
  },

  timeText(time) {
    if (!time) return ''
    const d = new Date(time)
    if (isNaN(d.getTime())) return ''
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`
  },

  // 展开/收起一轮练习的错题
  togglePractice(e) {
    const id = e.currentTarget.dataset.id
    const groups = this.data.practiceGroups
    let gi = -1
    let ii = -1
    for (let g = 0; g < groups.length; g++) {
      const i = groups[g].items.findIndex((x) => x.id === id)
      if (i > -1) { gi = g; ii = i; break }
    }
    if (gi < 0) return
    const item = groups[gi].items[ii]

    // 已加载过错题:直接展开/收起
    if (item.wrongQuestions.length) {
      const next = groups.map((g, gix) => gix === gi
        ? { ...g, items: g.items.map((it, iix) => iix === ii ? { ...it, expanded: !it.expanded } : it) }
        : g)
      this.setData({ practiceGroups: next })
      return
    }

    // 首次展开:懒加载该轮错题
    app.request({ url: `/sessions/${id}` })
      .then((res) => {
        const qByid = {}
        ;(res.questions || []).forEach((q) => { qByid[q.id] = q })
        const wrongQuestions = (res.answers || [])
          .filter((a) => !a.is_correct)
          .map((a) => {
            const q = qByid[a.question_id] || {}
            return { question_id: a.question_id, stem: q.stem || '', user_answer: a.user_answer || [] }
          })
        const next = groups.map((g, gix) => gix === gi
          ? { ...g, items: g.items.map((it, iix) => iix === ii ? { ...it, wrongQuestions, expanded: true } : it) }
          : g)
        this.setData({ practiceGroups: next })
      })
      .catch(() => {})
  },

  // 练习错题 → 记录详情
  onOpenWrong(e) {
    const { questionid, useranswer } = e.currentTarget.dataset
    const userAnswer = encodeURIComponent(JSON.stringify(useranswer || []))
    wx.navigateTo({
      url: `/pages/explain/explain?questionId=${questionid}&userAnswer=${userAnswer}&isCorrect=false`
    })
  },

  // 模拟记录 → 重看报告
  onOpenMock(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/mock-report/mock-report?sessionId=${id}` })
  }
})
