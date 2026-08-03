/**模拟测试报告:成绩 + 估分 + 各科正确率 + 错题回顾 + 正向引导*/
const app = getApp()

Page({
  data: {
    loading: true,
    correctCount: 0,
    totalCount: 0,
    estScore: 0,
    isFullPaper: false,
    accuracyPercent: 0,
    subjects: [],
    wrongList: [],
    tip: '',
    weakSubject: ''
  },

  onLoad(options) {
    const sessionId = Number(options.sessionId) || 0
    if (!sessionId) {
      wx.showToast({ title: '会话不存在', icon: 'none' })
      wx.navigateBack()
      return
    }
    this._sessionId = sessionId
    this.fetchReport()
  },

  fetchReport() {
    app.request({ url: `/sessions/${this._sessionId}` })
      .then((res) => {
        const report = res.report || {}
        const questions = res.questions || []
        const answers = res.answers || []
        const qByid = {}
        questions.forEach((q) => { qByid[q.id] = q })

        // 错题列表
        const wrongList = answers
          .filter((a) => !a.is_correct)
          .map((a) => {
            const q = qByid[a.question_id] || {}
            return {
              question_id: a.question_id,
              stem: q.stem || '',
              user_answer: a.user_answer || [],
              userAnswerText: (a.user_answer || []).join('、'),
              correctAnswerText: (q.answer || []).join('、')
            }
          })

        // 正向引导:最低分科目以「提分空间」措辞呈现(诚实不回避 + 陪伴式语气)
        let tip = '这轮暴露的问题,正是下一阶段的练习方向。'
        let weakSubject = ''
        const subjects = report.subjects || []
        if (subjects.length) {
          const weakest = subjects[0]
          const pct = Math.round(weakest.accuracy * 100)
          if (pct < 100) {
            weakSubject = weakest.subject
            tip = `「${weakest.subject}」还有 ${100 - pct}% 的提分空间,下一个提分点就是它。`
          }
        }

        const total = report.total_count || 0
        const subjectRows = subjects.map((s) => ({
          subject: s.subject,
          correct: s.correct,
          total: s.total,
          accuracyPercent: Math.round(s.accuracy * 100)
        }))
        this.setData({
          loading: false,
          correctCount: report.correct_count || 0,
          totalCount: total,
          estScore: report.est_score || 0,
          isFullPaper: !!report.is_full_paper,
          accuracyPercent: total ? Math.round((report.correct_count || 0) / total * 100) : 0,
          subjects: subjectRows,
          wrongList,
          tip,
          weakSubject
        })
      })
      .catch((err) => {
        wx.showToast({ title: err || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  // 错题 → 记录详情
  onOpenWrong(e) {
    const { questionid, useranswer } = e.currentTarget.dataset
    const userAnswer = encodeURIComponent(JSON.stringify(useranswer || []))
    wx.navigateTo({
      url: `/pages/explain/explain?questionId=${questionid}&userAnswer=${userAnswer}&isCorrect=false`
    })
  },

  // 提分点直达:去练「X」(进配置页预选该科目,用户仍有选题量权力)
  onPracticeWeak() {
    if (!this.data.weakSubject) return
    wx.navigateTo({
      url: `/pages/practice-config/practice-config?subject=${encodeURIComponent(this.data.weakSubject)}`
    })
  },

  onAgain() {
    wx.redirectTo({ url: '/pages/mock-config/mock-config' })
  },

  onHome() {
    wx.switchTab({ url: '/pages/index/index' })
  }
})
