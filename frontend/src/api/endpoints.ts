import { apiClient } from './client'
import type { User } from '@/types/auth'

export const authApi = {
  login: async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
    const response = await apiClient.post<{ access_token: string; user: User }>('/auth/login', {
      username,
      password,
    })
    return response.data
  },

  validateToken: async (token: string): Promise<User> => {
    const response = await apiClient.post<User>('/auth/validate', {
      token,
    })
    return response.data
  },

  validateApiKey: async (apiKey: string): Promise<User> => {
    const response = await apiClient.post<User>('/auth/validate-key', {
      apiKey,
    })
    return response.data
  },

  getStatus: async (): Promise<{ authenticated: boolean; user: User | null }> => {
    const response = await apiClient.get<{
      authenticated: boolean
      user: User | null
    }>('/auth/status')
    return response.data
  },
}

export const agentApi = {
  generateCode: async (prompt: string, language?: string) => {
    const response = await apiClient.post('/agent/generate', {
      prompt,
      language,
    })
    return response.data
  },

  refactorCode: async (code: string, requirements: string) => {
    const response = await apiClient.post('/agent/refactor', {
      code,
      requirements,
    })
    return response.data
  },

  generateTests: async (code: string, framework: string) => {
    const response = await apiClient.post('/agent/test', {
      code,
      framework,
    })
    return response.data
  },

  explainCode: async (code: string) => {
    const response = await apiClient.post('/agent/explain', {
      code,
    })
    return response.data
  },

  fixBug: async (code: string, error: string) => {
    const response = await apiClient.post('/agent/fix', {
      code,
      error,
    })
    return response.data
  },

  chat: async (message: string, conversationId?: string) => {
    const response = await apiClient.post('/agent/chat', {
      message,
      conversation_id: conversationId,
    })
    return response.data
  },
}

export const healthApi = {
  checkHealth: async () => {
    const response = await apiClient.get('/health')
    return response.data
  },
}
