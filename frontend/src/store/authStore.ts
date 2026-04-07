import { create } from 'zustand'
import { storage } from '@/utils/storage'
import type { User, AuthState } from '@/types/auth'
// Note: Credentials are stored in sessionStorage (cleared on browser close) for security

interface AuthStore extends AuthState {
  login: (token: string, user: User) => void
  loginWithApiKey: (apiKey: string, user: User) => void
  logout: () => void
  setUser: (user: User) => void
  hydrate: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  token: null,
  apiKey: null,
  isAuthenticated: false,
  user: null,

  login: (token: string, user: User) => {
    storage.setToken(token)
    storage.setUser(user)
    set({
      token,
      user,
      apiKey: null,
      isAuthenticated: true,
    })
  },

  loginWithApiKey: (apiKey: string, user: User) => {
    storage.setApiKey(apiKey)
    storage.setUser(user)
    set({
      apiKey,
      user,
      token: null,
      isAuthenticated: true,
    })
  },

  logout: () => {
    storage.clear()
    set({
      token: null,
      apiKey: null,
      user: null,
      isAuthenticated: false,
    })
  },

  setUser: (user: User) => {
    storage.setUser(user)
    set({ user })
  },

  hydrate: () => {
    const token = storage.getToken()
    const apiKey = storage.getApiKey()
    const user = storage.getUser()

    if ((token || apiKey) && user) {
      set({
        token: token || null,
        apiKey: apiKey || null,
        user,
        isAuthenticated: true,
      })
    }
  },
}))
