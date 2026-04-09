import axios, { AxiosInstance, AxiosError } from 'axios'
import toast from 'react-hot-toast'
import { API_BASE_URL, AUTH_HEADERS, HTTP_STATUS } from '@/utils/constants'
import { useAuthStore } from '@/store/authStore'

// Per-action timeout configuration (in milliseconds)
export const ACTION_TIMEOUTS: Record<string, number> = {
  chat: 120_000,      // 2 minutes
  generate: 90_000,   // 1.5 minutes
  refactor: 60_000,   // 1 minute
  test: 60_000,
  explain: 45_000,
  fix: 60_000,
  default: 30_000,
}

export const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000,  // Increased from 30s to 2m as default
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      const authStore = useAuthStore.getState()

      if (authStore.token) {
        config.headers.Authorization = `${AUTH_HEADERS.BEARER} ${authStore.token}`
      } else if (authStore.apiKey) {
        config.headers[AUTH_HEADERS.API_KEY] = authStore.apiKey
      }

      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      const authStore = useAuthStore.getState()

      // Handle 401 Unauthorized
      if (error.response?.status === HTTP_STATUS.UNAUTHORIZED) {
        authStore.logout()
        toast.error('Session expired. Please login again.')
        // Let the router component (App.tsx) handle redirect via auth state change
      }

      // Handle 403 Forbidden
      if (error.response?.status === HTTP_STATUS.FORBIDDEN) {
        toast.error('You do not have permission to access this resource.')
      }

      // Handle 500 Internal Server Error
      if (error.response?.status === HTTP_STATUS.INTERNAL_ERROR) {
        toast.error('Server error. Please try again later.')
      }

      return Promise.reject(error)
    }
  )

  return client
}

export const apiClient = createApiClient()
