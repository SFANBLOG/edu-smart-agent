import axios from 'axios'

// baseURL '/api'：开发期由 Vite proxy 转发到 FastAPI；生产期同源
const client = axios.create({ baseURL: '/api', timeout: 120000 })

client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.error ||
      error?.message ||
      '请求失败'
    return Promise.reject(new Error(message))
  },
)

export default client
