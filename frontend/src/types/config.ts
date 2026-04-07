export type SettingType = 'string' | 'number' | 'boolean' | 'enum'

export interface SettingMetadata {
  name: string
  description?: string
  type: SettingType
  options?: string[] // For enum type
  min?: number // For number type
  max?: number // For number type
  step?: number // For number type
}

export type ConfigSettings = Record<string, any>

export interface ConfigResponse {
  [key: string]: any
}

export interface UpdateConfigRequest {
  value: any
}

export interface ResetConfigResponse {
  message: string
  config: ConfigSettings
}

export interface ConfigPageState {
  config: ConfigSettings | null
  loading: boolean
  error: string | null
  isAdmin: boolean
}

export interface SettingFieldProps {
  name: string
  value: any
  onChange: (key: string, value: any) => void
  onBlur?: (key: string) => void
  type?: SettingType
  metadata?: SettingMetadata
  isUpdating?: boolean
}
