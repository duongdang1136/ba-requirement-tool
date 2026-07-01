import axios from 'axios'

const api = axios.create({
  // Vite proxies /api to the FastAPI backend on localhost:8099.
  baseURL: '/api',
})

export default api
