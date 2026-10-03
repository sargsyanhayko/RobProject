import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      if (window.location.pathname.startsWith('/admin') && window.location.pathname !== '/admin/login') {
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(error)
  },
)

export default api

export async function login(username, password) {
  const { data } = await api.post('/api/auth/login', { username, password })
  localStorage.setItem('admin_token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('admin_token')
}

export function getProducts(skip = 0, limit = 50) {
  return api.get('/api/products', { params: { skip, limit } })
}

export function getProduct(id) {
  return api.get(`/api/products/${id}`)
}

export function createProduct(product) {
  return api.post('/api/admin/products', product)
}

export function updateProduct(id, product) {
  return api.patch(`/api/admin/products/${id}`, product)
}

export function deleteProduct(id) {
  return api.delete(`/api/admin/products/${id}`)
}
