import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/store/authStore'

vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('@/api/endpoints', () => ({
  authApi: {
    validateToken: vi.fn(),
    validateApiKey: vi.fn(),
  },
}))

describe('useAuth hook', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: null,
      apiKey: null,
      isAuthenticated: false,
      user: null,
    })
  })

  it('should have initial state', () => {
    const { result } = renderHook(() => useAuth())

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.token).toBe(null)
    expect(result.current.apiKey).toBe(null)
    expect(result.current.user).toBe(null)
  })

  it('should have logout function', () => {
    const { result } = renderHook(() => useAuth())

    expect(typeof result.current.logout).toBe('function')
  })

  it('should have login functions', () => {
    const { result } = renderHook(() => useAuth())

    expect(typeof result.current.loginWithToken).toBe('function')
    expect(typeof result.current.loginWithApiKey).toBe('function')
  })
})
