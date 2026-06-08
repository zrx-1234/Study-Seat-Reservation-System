import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动携带 JWT
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('student_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const { response } = error
    if (response) {
      const status = response.status
      let msg = response.data?.message
      if (!msg) {
        if (status === 401) msg = '账号或密码错误，或登录已过期'
        else if (status === 409) msg = '该学号已注册，请直接登录'
        else if (status === 502 || status === 503 || status === 504) msg = '后端服务不可用，请确认后端已启动'
        else if (status >= 500) msg = '服务器错误，请稍后再试'
        else msg = '请求失败'
      }
      if (status === 401) {
        const token = localStorage.getItem('student_token')
        if (token) {
          ElMessage.error('登录已过期，请重新登录')
        } else {
          ElMessage.error(msg)
        }
        localStorage.removeItem('student_token')
        localStorage.removeItem('student_user')
        const base = import.meta.env.BASE_URL || '/'
        window.location.href = base.replace(/\/$/, '') + '/login'
      } else {
        ElMessage.error(msg)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
