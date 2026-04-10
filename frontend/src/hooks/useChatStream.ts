import { useState, useCallback, useRef } from 'react'
import toast from 'react-hot-toast'
import { API_BASE_URL } from '@/utils/constants'
import { useAuthStore } from '@/store/authStore'
import type { ChatRequest } from '@/types/actions'

interface StreamStats {
  executionTime: number
  tokensUsed: {
    input: number
    output: number
    total: number
  }
}

interface UseChatStreamState {
  progress: string[]
  isStreaming: boolean
  stats: StreamStats | undefined
  error: string | null
}

export const useChatStream = () => {
  const [state, setState] = useState<UseChatStreamState>({
    progress: [],
    isStreaming: false,
    stats: undefined,
    error: null,
  })

  // AbortController to cancel stream
  const abortRef = useRef<AbortController | null>(null)

  const sendChatStream = useCallback(
    async (params: ChatRequest, onProgress?: (message: string) => void, onToken?: (content: string) => void): Promise<{ content: string; stats: StreamStats | undefined } | null> => {
      // Abort previous stream if still in progress
      abortRef.current?.abort()
      abortRef.current = new AbortController()

      setState({
        progress: [],
        isStreaming: true,
        stats: undefined,
        error: null,
      })

      try {
        const authStore = useAuthStore.getState()
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }

        // Add auth header (fetch requires full header format, not like axios interceptor)
        if (authStore.token) {
          headers['Authorization'] = `Bearer ${authStore.token}`
        } else if (authStore.apiKey) {
          headers['X-API-Key'] = authStore.apiKey
        }

        const response = await fetch(`${API_BASE_URL}/agent/chat-stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify(params),
          signal: abortRef.current.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let fullContent = ''
        let streamStats: StreamStats | undefined = undefined

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n').filter((line) => line.trim())

          for (const line of lines) {
            // SSE format: "data: {...}"
            if (!line.startsWith('data: ')) continue

            const eventStr = line.slice(6).trim()
            if (!eventStr) continue

            const data = JSON.parse(eventStr)

            if (data.type === 'progress') {
              // Emit progress messages for UI display
              setState((prev) => ({
                ...prev,
                progress: [...prev.progress, data.message],
              }))
              // Notify caller via callback (for workflow real-time updates)
              onProgress?.(data.message)
            } else if (data.type === 'token') {
              // Accumulate response content (multiple tokens can be streamed)
              if (data.content) {
                fullContent += data.content
                onToken?.(fullContent)
              }
            } else if (data.type === 'complete') {
              // Stream complete with stats
              // Use response from complete event if available, otherwise use accumulated content
              if (data.response) {
                fullContent = data.response
              }
              streamStats =
                data.tokens_used && data.execution_time
                  ? {
                      executionTime: data.execution_time,
                      tokensUsed: {
                        input: data.tokens_used.input || 0,
                        output: data.tokens_used.output || 0,
                        total: data.tokens_used.total || 0,
                      },
                    }
                  : undefined
              setState((prev) => ({
                ...prev,
                isStreaming: false,
                stats: streamStats,
              }))
              return { content: fullContent, stats: streamStats }
            } else if (data.type === 'error') {
              throw new Error(data.message || 'Stream error')
            }
          }
        }

        // If we get here without a 'done' event, stream ended unexpectedly
        setState((prev) => ({
          ...prev,
          isStreaming: false,
        }))

        return { content: fullContent, stats: streamStats || undefined }
      } catch (error) {
        // Cancelled stream — no error toast
        if (error instanceof Error && error.name === 'AbortError') {
          setState({
            progress: [],
            isStreaming: false,
            stats: undefined,
            error: null,
          })
          return null
        }

        const errorMessage = error instanceof Error ? error.message : 'Stream failed'
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: errorMessage,
        }))

        toast.error(errorMessage)
        throw error
      }
    },
    []
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState({
      progress: [],
      isStreaming: false,
      stats: undefined,
      error: null,
    })
  }, [])

  const reset = useCallback(() => {
    setState({
      progress: [],
      isStreaming: false,
      stats: undefined,
      error: null,
    })
  }, [])

  return {
    ...state,
    sendChatStream,
    cancel,
    reset,
  }
}
