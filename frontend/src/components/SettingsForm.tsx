import { useState } from 'react'
import { LoadingSpinner } from './LoadingSpinner'
import type { ConfigSettings } from '@/types/config'

interface SettingsFormProps {
  settings: ConfigSettings | null
  onUpdateSetting: (key: string, value: any) => Promise<any>
  onReset: () => Promise<any>
  isLoading: boolean
  isAdmin: boolean
  updatingKeys: Set<string>
}

// Categorize settings based on key prefix
const getCategoryFromKey = (key: string): string => {
  if (key.startsWith('jm_')) return 'Agent Settings'
  if (key.startsWith('host') || key.startsWith('port') || key === 'debug')
    return 'Server Settings'
  if (key.includes('enable') || key.includes('flag')) return 'Feature Flags'
  if (key.includes('log')) return 'Logging'
  return 'Other Settings'
}

// Infer field type from value
const inferFieldType = (value: any): 'string' | 'number' | 'boolean' => {
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  return 'string'
}

// Format label from key (jm_default_model -> Default Model)
const formatLabel = (key: string): string => {
  return key
    .replace(/^jm_/, '')
    .replace(/_/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export const SettingsForm = ({
  settings,
  onUpdateSetting,
  onReset,
  isLoading,
  isAdmin,
  updatingKeys,
}: SettingsFormProps) => {
  const [localValues, setLocalValues] = useState<Record<string, any>>(settings || {})
  const [resetLoading, setResetLoading] = useState(false)

  // Update local value on input change
  const handleChange = (key: string, value: any) => {
    setLocalValues((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  // Send update to API when field loses focus
  const handleBlur = async (key: string) => {
    const newValue = localValues[key]
    const oldValue = settings?.[key]

    if (newValue !== oldValue) {
      try {
        await onUpdateSetting(key, newValue)
      } catch {
        // On error, revert to old value
        setLocalValues((prev) => ({
          ...prev,
          [key]: oldValue,
        }))
      }
    }
  }

  // Handle reset button
  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      setResetLoading(true)
      try {
        await onReset()
        setLocalValues(settings || {})
      } finally {
        setResetLoading(false)
      }
    }
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!settings) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600">No settings available</p>
      </div>
    )
  }

  // Group settings by category
  const categories: Record<string, [string, any][]> = {}
  Object.entries(settings).forEach(([key, value]) => {
    const category = getCategoryFromKey(key)
    if (!categories[category]) {
      categories[category] = []
    }
    categories[category].push([key, value])
  })

  return (
    <div className="space-y-8">
      {Object.entries(categories).map(([category, items]) => (
        <section key={category}>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">{category}</h2>

          <div className="bg-white rounded-lg shadow divide-y">
            {items.map(([key, originalValue]) => {
              const fieldType = inferFieldType(originalValue)
              const currentValue = localValues[key] ?? originalValue
              const isUpdating = updatingKeys.has(key)

              return (
                <div key={key} className="p-6 flex items-center justify-between">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-slate-900">
                      {formatLabel(key)}
                    </label>
                    <p className="text-xs text-slate-500 mt-1">Key: {key}</p>
                  </div>

                  <div className="flex-1 ml-6 flex items-center gap-3">
                    {fieldType === 'boolean' ? (
                      <button
                        onClick={() => {
                          const newValue = !currentValue
                          handleChange(key, newValue)
                          handleBlur(key)
                        }}
                        disabled={isUpdating}
                        className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                          currentValue
                            ? 'bg-primary-500'
                            : 'bg-slate-300'
                        } ${isUpdating ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <span
                          className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                            currentValue ? 'translate-x-7' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    ) : fieldType === 'number' ? (
                      <input
                        type="number"
                        value={currentValue}
                        onChange={(e) =>
                          handleChange(key, parseFloat(e.target.value))
                        }
                        onBlur={() => handleBlur(key)}
                        disabled={isUpdating}
                        className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
                        step="0.01"
                      />
                    ) : (
                      <input
                        type="text"
                        value={currentValue}
                        onChange={(e) => handleChange(key, e.target.value)}
                        onBlur={() => handleBlur(key)}
                        disabled={isUpdating}
                        className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
                      />
                    )}

                    {isUpdating && (
                      <div className="ml-2">
                        <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      ))}

      {isAdmin && (
        <div className="flex justify-end pt-6 border-t border-slate-200">
          <button
            onClick={handleReset}
            disabled={resetLoading}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-red-400 disabled:cursor-not-allowed"
          >
            {resetLoading ? 'Resetting...' : 'Reset All Settings'}
          </button>
        </div>
      )}
    </div>
  )
}
