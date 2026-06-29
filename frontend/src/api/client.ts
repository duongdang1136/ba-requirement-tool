import axios from 'axios'

const api = axios.create({
  // Docker: nginx proxies /api/ → backend
  // Dev: vite proxy /api → localhost:8099
  baseURL: '/api',
})

export default api
