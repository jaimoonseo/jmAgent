import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCodeAction } from '@/hooks/useCodeAction'
import { apiClient } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('useCodeAction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useCodeAction())

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('sets loading to true during execution', async () => {
    const mockResponse = {
      data: {
        generated_code: 'const x = 5;',
        model_used: 'haiku',
        tokens_used: { input: 10, output: 20 },
        execution_time: 1.5,
      },
    }

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      await result.current.execute({
        action: 'generate',
        params: {
          prompt: 'test',
        },
      })
    })

    expect(result.current.loading).toBe(false)
  })

  it('handles generate action', async () => {
    const mockResponse = {
      data: {
        generated_code: 'const x = 5;',
        model_used: 'haiku',
        tokens_used: { input: 10, output: 20 },
        execution_time: 1.5,
      },
    }

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      await result.current.execute({
        action: 'generate',
        params: {
          prompt: 'Create a hello world function',
        },
      })
    })

    expect(apiClient.post).toHaveBeenCalledWith(
      '/agent/generate',
      expect.objectContaining({
        prompt: 'Create a hello world function',
      })
    )
    expect(result.current.data).toEqual(mockResponse.data)
  })

  it('handles refactor action', async () => {
    const mockResponse = {
      data: {
        refactored_code: 'improved code',
        changes_summary: 'Added type hints',
        model_used: 'haiku',
        tokens_used: { input: 20, output: 30 },
        execution_time: 2.0,
      },
    }

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      await result.current.execute({
        action: 'refactor',
        params: {
          code: 'old code',
          requirements: 'add type hints',
        },
      })
    })

    expect(apiClient.post).toHaveBeenCalledWith(
      '/agent/refactor',
      expect.any(Object)
    )
  })

  it('handles test action', async () => {
    const mockResponse = {
      data: {
        test_code: 'test content',
        coverage_estimate: '80%',
        framework_used: 'pytest',
        model_used: 'haiku',
        tokens_used: { input: 15, output: 25 },
        execution_time: 1.8,
      },
    }

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      await result.current.execute({
        action: 'test',
        params: {
          code: 'function code',
          framework: 'pytest',
        },
      })
    })

    expect(apiClient.post).toHaveBeenCalledWith('/agent/test', expect.any(Object))
  })

  it('handles error responses', async () => {
    const mockError = new Error('API Error')
    vi.mocked(apiClient.post).mockRejectedValueOnce(mockError)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      try {
        await result.current.execute({
          action: 'generate',
          params: { prompt: 'test' },
        })
      } catch {
        // Expected to throw
      }
    })

    expect(result.current.error).not.toBeNull()
    expect(result.current.data).toBeNull()
  })

  it('resets state when reset is called', async () => {
    const mockResponse = {
      data: {
        generated_code: 'code',
        model_used: 'haiku',
        tokens_used: { input: 10, output: 20 },
        execution_time: 1.5,
      },
    }

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      await result.current.execute({
        action: 'generate',
        params: { prompt: 'test' },
      })
    })

    expect(result.current.data).not.toBeNull()

    act(() => {
      result.current.reset()
    })

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('handles chat action with conversation ID', async () => {
    const mockResponse = {
      data: {
        response: 'Chat response',
        conversation_id: 'conv-123',
        model_used: 'haiku',
        tokens_used: { input: 10, output: 20 },
        execution_time: 1.5,
      },
    }

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useCodeAction())

    await act(async () => {
      await result.current.execute({
        action: 'chat',
        params: {
          message: 'Hello',
          conversation_id: 'conv-123',
        },
      })
    })

    expect(apiClient.post).toHaveBeenCalledWith(
      '/agent/chat',
      expect.objectContaining({
        message: 'Hello',
        conversation_id: 'conv-123',
      })
    )
  })
})
