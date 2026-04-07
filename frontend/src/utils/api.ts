import { apiClient } from '@/api/client'
import type { ConfigSettings, ConfigResponse, ResetConfigResponse } from '@/types/config'

export const getConfig = async (): Promise<ConfigSettings> => {
  const response = await apiClient.get<ConfigResponse>('/config')
  return response.data
}

export const updateConfigSetting = async (
  key: string,
  value: any
): Promise<ConfigResponse> => {
  const response = await apiClient.put<ConfigResponse>(`/config/${key}`, {
    value,
  })
  return response.data
}

export const resetAllSettings = async (): Promise<ResetConfigResponse> => {
  const response = await apiClient.post<ResetConfigResponse>('/config/reset')
  return response.data
}
