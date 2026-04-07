export type UserRole = 'admin' | 'user' | 'guest'

export interface User {
  id: string
  role: UserRole
  email?: string
  name?: string
}

export interface AuthState {
  token: string | null
  apiKey: string | null
  isAuthenticated: boolean
  user: User | null
}

export interface LoginResponse {
  token: string
  user: User
}

export interface ApiKeyResponse {
  apiKey: string
  message: string
}
