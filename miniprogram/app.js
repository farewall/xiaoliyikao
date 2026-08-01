/**app.js - 小鲤医考全局入口*/
App({
  globalData: {
    userInfo: null,
    // 后端地址:开发期指向本地 Docker;部署后替换为备案域名
    baseUrl: 'http://localhost:8000'
  },

  onLaunch() {
    // 登录:换后端 openid(开发期后端会用 code 占位)
    this.login()
  },

  login() {
    wx.login({
      success: (res) => {
        if (!res.code) return
        this.request({
          url: '/users/login',
          method: 'POST',
          data: { code: res.code },
          success: (user) => {
            this.globalData.userInfo = user
          }
        })
      }
    })
  },

  /**
   * 统一的请求封装:拼 baseUrl + 返回 Promise。
   * 小程序需在「不校验合法域名」下访问本地地址(开发期)。
   */
  request(options) {
    const { url, method = 'GET', data = {}, header = {} } = options
    return new Promise((resolve, reject) => {
      wx.request({
        url: this.globalData.baseUrl + url,
        method,
        data,
        header: { 'content-type': 'application/json', ...header },
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data)
          } else {
            // 后端错误信息透传
            reject(res.data?.detail || `请求失败(${res.statusCode})`)
          }
        },
        fail: (err) => reject(err.errMsg || '网络异常')
      })
    })
  }
})
