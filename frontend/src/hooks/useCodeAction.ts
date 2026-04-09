import { useState, useCallback, useRef } from 'react'
import axios, { AxiosError } from 'axios'
import toast from 'react-hot-toast'
import { apiClient, ACTION_TIMEOUTS } from '@/api/client'
import type {
  GenerateRequest,
  GenerateResponse,
  RefactorRequest,
  RefactorResponse,
  TestRequest,
  TestResponse,
  ExplainRequest,
  ExplainResponse,
  FixRequest,
  FixResponse,
  ChatRequest,
  ChatResponse,
  ActionResponse,
} from '@/types/actions'

type CodeActionRequest =
  | { action: 'generate'; params: GenerateRequest }
  | { action: 'refactor'; params: RefactorRequest }
  | { action: 'test'; params: TestRequest }
  | { action: 'explain'; params: ExplainRequest }
  | { action: 'fix'; params: FixRequest }
  | { action: 'chat'; params: ChatRequest }

interface UseCodeActionState {
  data: ActionResponse | null
  loading: boolean
  error: AxiosError | null
}

export const useCodeAction = () => {
  const [state, setState] = useState<UseCodeActionState>({
    data: null,
    loading: false,
    error: null,
  })

  // AbortController to cancel previous request when new one starts
  const abortRef = useRef<AbortController | null>(null)

  const execute = useCallback(async (request: CodeActionRequest) => {
    // Abort previous request if still in progress
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setState({ data: null, loading: true, error: null })

    // Get per-action timeout
    const timeout = ACTION_TIMEOUTS[request.action] ?? ACTION_TIMEOUTS.default

    try {
      let response
      switch (request.action) {
        case 'generate':
          response = await apiClient.post<GenerateResponse>(
            '/agent/generate',
            request.params,
            { timeout, signal: abortRef.current.signal }
          )
          break
        case 'refactor':
          response = await apiClient.post<RefactorResponse>(
            '/agent/refactor',
            request.params,
            { timeout, signal: abortRef.current.signal }
          )
          break
        case 'test':
          response = await apiClient.post<TestResponse>(
            '/agent/test',
            request.params,
            { timeout, signal: abortRef.current.signal }
          )
          break
        case 'explain':
          response = await apiClient.post<ExplainResponse>(
            '/agent/explain',
            request.params,
            { timeout, signal: abortRef.current.signal }
          )
          break
        case 'fix':
          response = await apiClient.post<FixResponse>(
            '/agent/fix',
            request.params,
            { timeout, signal: abortRef.current.signal }
          )
          break
        case 'chat':
          response = await apiClient.post<ChatResponse>(
            '/agent/chat',
            request.params,
            { timeout, signal: abortRef.current.signal }
          )
          break
        default:
          throw new Error('Invalid action')
      }

      // Backend wraps response in APIResponse { success, data, error, ... }
      // Extract the actual data payload
      const actualData = (response.data as any).data || response.data
      setState({ data: actualData, loading: false, error: null })
      return actualData
    } catch (error) {
      // Cancelled request — no token spent, no error toast
      if (axios.isCancel(error)) {
        setState({ data: null, loading: false, error: null })
        return null
      }

      const axiosError = error as AxiosError
      setState({ data: null, loading: false, error: axiosError })

      // Show error toast
      const errorMessage =
        (axiosError.response?.data as any)?.detail ||
        axiosError.message ||
        'An error occurred'
      toast.error(errorMessage)

      throw axiosError
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState({ data: null, loading: false, error: null })
  }, [])

  return {
    ...state,
    execute,
    reset,
    cancel,
  }
}
