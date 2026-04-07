import { useState, useCallback } from 'react'
import { AxiosError } from 'axios'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: AxiosError | null
}

export const useApi = <T,>() => {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async (apiCall: () => Promise<T>) => {
    setState({ data: null, loading: true, error: null })

    try {
      const response = await apiCall()
      setState({ data: response, loading: false, error: null })
      return response
    } catch (error) {
      const axiosError = error as AxiosError
      setState({ data: null, loading: false, error: axiosError })
      throw axiosError
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return {
    ...state,
    execute,
    reset,
  }
}
