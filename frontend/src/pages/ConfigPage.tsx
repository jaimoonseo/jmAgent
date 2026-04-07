import { Sidebar } from '@/components/Sidebar'
import { SettingsForm } from '@/components/SettingsForm'
import { useConfig } from '@/hooks/useConfig'

export const ConfigPage = () => {
  const { config, loading, error, isAdmin, updatingKeys, updateSetting, resetAll } =
    useConfig()

  return (
    <>
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-slate-900 mb-2">Configuration</h1>
            <p className="text-slate-600 mb-8">
              Manage jmAgent settings and configuration. Changes are applied immediately.
            </p>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700">Failed to load configuration: {error}</p>
              </div>
            )}

            <div className="bg-white rounded-lg shadow p-8">
              <SettingsForm
                settings={config}
                onUpdateSetting={updateSetting}
                onReset={resetAll}
                isLoading={loading}
                isAdmin={isAdmin}
                updatingKeys={updatingKeys}
              />
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
