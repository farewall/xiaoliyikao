/**app.js - 小鲤医考全局入口*/
App({
  globalData: {
    userInfo: null,
    // 后端地址:开发期指向本地后端;部署后替换为备案域名
    baseUrl: 'http://localhost:8000'
  },

  onLaunch() {
    // 登录:换后端 openid(开发期后端会用 code 占位)
    this.login()
  },

  login() {
    return new Promise((resolve) => {
      wx.login({
        success: (res) => {
          if (!res.code) { resolve(null); return }
          this.request({
            url: '/users/login',
            method: 'POST',
            data: { code: res.code }
          })
            .then((data) => {
              // data = { token, user }:保存 JWT,后续请求自动携带
              this.globalData.userInfo = data.user
              wx.setStorageSync('token', data.token)
              resolve(data)
            })
            .catch(() => resolve(null))
        },
        fail: () => resolve(null)
      })
    })
  },

  /**
   * 统一的请求封装:拼 baseUrl + 自动携带 token + 返回 Promise。
   * - 401 时清 token 并重新登录(登录态失效)。
   * - 小程序需在「不校验合法域名」下访问本地地址(开发期)。
   */
  request(options) {
    const { url, method = 'GET', data = {}, header = {} } = options
    const token = wx.getStorageSync('token')
    return new Promise((resolve, reject) => {
      wx.request({
        url: this.globalData.baseUrl + url,
        method,
        data,
        header: {
          'content-type': 'application/json',
          Authorization: token ? `Bearer ${token}` : '',
          ...header
        },
        success: (res) => {
          if (res.statusCode === 401) {
            // 登录态失效:清掉 token 重新登录
            wx.removeStorageSync('token')
            this.login()
            reject(res.data?.detail || '登录已过期')
            return
          }
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
