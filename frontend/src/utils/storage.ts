import { AUTH_STORAGE_KEYS } from './constants'
import type { User } from '@/types/auth'

export const storage = {
  setToken: (token: string) => {
    sessionStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, token)
  },

  getToken: (): string | null => {
    return sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
  },

  removeToken: () => {
    sessionStorage.removeItem(AUTH_STORAGE_KEYS.TOKEN)
  },

  setApiKey: (apiKey: string) => {
    sessionStorage.setItem(AUTH_STORAGE_KEYS.API_KEY, apiKey)
  },

  getApiKey: (): string | null => {
    return sessionStorage.getItem(AUTH_STORAGE_KEYS.API_KEY)
  },

  removeApiKey: () => {
    sessionStorage.removeItem(AUTH_STORAGE_KEYS.API_KEY)
  },

  setUser: (user: User) => {
    sessionStorage.setItem(AUTH_STORAGE_KEYS.USER, JSON.stringify(user))
  },

  getUser: (): User | null => {
    const user = sessionStorage.getItem(AUTH_STORAGE_KEYS.USER)
    try {
      return user ? JSON.parse(user) : null
    } catch (error) {
      console.warn('Failed to parse stored user data:', error)
      return null
    }
  },

  removeUser: () => {
    sessionStorage.removeItem(AUTH_STORAGE_KEYS.USER)
  },

  clear: () => {
    sessionStorage.removeItem(AUTH_STORAGE_KEYS.TOKEN)
    sessionStorage.removeItem(AUTH_STORAGE_KEYS.API_KEY)
    sessionStorage.removeItem(AUTH_STORAGE_KEYS.USER)
  },
}
