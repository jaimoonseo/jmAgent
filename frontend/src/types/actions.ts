export type Model = 'haiku' | 'sonnet' | 'opus'
export type Framework = 'pytest' | 'vitest' | 'jest'
export type Language = 'en' | 'ko'

// Request types
export interface GenerateRequest {
  prompt: string
  model?: Model
  temperature?: number
  max_tokens?: number
}

export interface RefactorRequest {
  code: string
  requirements: string
  model?: Model
  temperature?: number
  max_tokens?: number
}

export interface TestRequest {
  code: string
  framework: Framework
  model?: Model
  temperature?: number
  max_tokens?: number
}

export interface ExplainRequest {
  code: string
  focus_area?: string
  language?: Language
  model?: Model
}

export interface FixRequest {
  code: string
  error: string
  model?: Model
  temperature?: number
  max_tokens?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  model?: Model
  temperature?: number
  max_tokens?: number
}

// Response types
export interface TokensUsed {
  input: number
  output: number
}

export interface GenerateResponse {
  generated_code: string
  model_used: string
  tokens_used: TokensUsed
  execution_time: number
}

export interface RefactorResponse {
  refactored_code: string
  changes_summary: string
  model_used: string
  tokens_used: TokensUsed
  execution_time: number
}

export interface TestResponse {
  test_code: string
  coverage_estimate?: string
  framework_used: string
  model_used: string
  tokens_used: TokensUsed
  execution_time: number
}

export interface ExplainResponse {
  explanation: string
  key_concepts: string[]
  model_used: string
  tokens_used: TokensUsed
  execution_time: number
}

export interface FixResponse {
  fixed_code: string
  fix_summary: string
  model_used: string
  tokens_used: TokensUsed
  execution_time: number
}

export interface ChatResponse {
  response: string
  conversation_id: string
  model_used: string
  tokens_used: TokensUsed
  execution_time: number
}

// Unified action result type
export type ActionResponse =
  | GenerateResponse
  | RefactorResponse
  | TestResponse
  | ExplainResponse
  | FixResponse
  | ChatResponse
