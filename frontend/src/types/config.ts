export type SettingValue = string | number | boolean

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

export type ConfigSettings = Record<string, SettingValue>

export interface ConfigResponse {
  [key: string]: SettingValue
}

export interface UpdateConfigRequest {
  value: SettingValue
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
  value: SettingValue
  onChange: (key: string, value: SettingValue) => void
  onBlur?: (key: string) => void
  type?: SettingType
  metadata?: SettingMetadata
  isUpdating?: boolean
}
