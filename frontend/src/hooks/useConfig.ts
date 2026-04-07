import { useState, useCallback, useEffect } from 'react'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'
import { getConfig, updateConfigSetting, resetAllSettings } from '@/utils/api'
import type { ConfigSettings, SettingValue } from '@/types/config'

interface UseConfigState {
  config: ConfigSettings | null
  loading: boolean
  error: string | null
  updatingKeys: Set<string>
  isAdmin: boolean
}

export const useConfig = () => {
  const { user } = useAuthStore()
  const [state, setState] = useState<UseConfigState>({
    config: null,
    loading: true,
    error: null,
    updatingKeys: new Set(),
    isAdmin: user?.role === 'admin' || false,
  })

  // Fetch config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setState((prev) => ({
          ...prev,
          loading: true,
          error: null,
        }))
        const data = await getConfig()
        setState((prev) => ({
          ...prev,
          config: data,
          loading: false,
          error: null,
        }))
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to load configuration'
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }))
      }
    }

    fetchConfig()
  }, [])

  const updateSetting = useCallback(
    async (key: string, value: SettingValue) => {
      setState((prev) => ({
        ...prev,
        updatingKeys: new Set([...prev.updatingKeys, key]),
      }))

      try {
        const updated = await updateConfigSetting(key, value)
        setState((prev) => ({
          ...prev,
          config: { ...prev.config, ...updated },
          updatingKeys: new Set([...prev.updatingKeys].filter((k) => k !== key)),
        }))
        toast.success(`${key} updated successfully`)
        return updated
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update setting'
        toast.error(`Failed to update ${key}: ${errorMessage}`)
        setState((prev) => ({
          ...prev,
          updatingKeys: new Set([...prev.updatingKeys].filter((k) => k !== key)),
        }))
        throw error
      }
    },
    []
  )

  const resetAll = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      loading: true,
    }))

    try {
      const result = await resetAllSettings()
      setState((prev) => ({
        ...prev,
        config: result.config,
        loading: false,
        error: null,
      }))
      toast.success('All settings reset to defaults')
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reset settings'
      toast.error(`Failed to reset settings: ${errorMessage}`)
      setState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      throw error
    }
  }, [])

  return {
    config: state.config,
    loading: state.loading,
    error: state.error,
    isAdmin: state.isAdmin,
    updatingKeys: state.updatingKeys,
    updateSetting,
    resetAll,
  }
}
