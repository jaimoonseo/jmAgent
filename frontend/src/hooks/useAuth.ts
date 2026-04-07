import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/endpoints'
import toast from 'react-hot-toast'
import type { User } from '@/types/auth'

export const useAuth = () => {
  const navigate = useNavigate()
  const authStore = useAuthStore()

  const loginWithToken = useCallback(
    async (token: string) => {
      try {
        const user = await authApi.validateToken(token)
        authStore.login(token, user)
        toast.success('Login successful!')
        navigate('/dashboard')
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Invalid token'
        toast.error(message)
        throw error
      }
    },
    [authStore, navigate]
  )

  const loginWithApiKey = useCallback(
    async (apiKey: string) => {
      try {
        const user = await authApi.validateApiKey(apiKey)
        authStore.loginWithApiKey(apiKey, user)
        toast.success('Login successful!')
        navigate('/dashboard')
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Invalid API key'
        toast.error(message)
        throw error
      }
    },
    [authStore, navigate]
  )

  const logout = useCallback(() => {
    authStore.logout()
    toast.success('Logged out successfully')
    navigate('/login')
  }, [authStore, navigate])

  const updateUser = useCallback(
    (user: User) => {
      authStore.setUser(user)
    },
    [authStore]
  )

  return {
    ...authStore,
    loginWithToken,
    loginWithApiKey,
    logout,
    updateUser,
  }
}
