import { useState } from 'react'
import { CodeOutput } from '@/components/CodeOutput'
import { ModelSelector } from '@/components/ModelSelector'
import { ExecutionStats } from '@/components/ExecutionStats'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useCodeAction } from '@/hooks/useCodeAction'
import type { Model, GenerateResponse } from '@/types/actions'

export const GeneratePage = () => {
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState<Model>('haiku')
  const [temperature, setTemperature] = useState(0.2)
  const [maxTokens, setMaxTokens] = useState(4096)
  const { data, loading, error, execute, reset } = useCodeAction()

  const result = data as GenerateResponse | null

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      return
    }
    await execute({
      action: 'generate',
      params: {
        prompt,
        model,
        temperature,
        max_tokens: maxTokens,
      },
    })
  }

  return (
    <div className="flex-1 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Generate Code</h1>
        <p className="text-slate-600 mb-8">
          Describe what you want to create, and Claude will generate code for you.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-3">
                  Describe what you want to generate
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Create a FastAPI GET endpoint that returns a list of users from a database..."
                  className="w-full h-32 p-4 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <ModelSelector value={model} onChange={setModel} />

                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-slate-900">
                    Temperature
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="flex-1 h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-sm font-mono text-slate-600 w-8">
                      {temperature.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-900">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  min="256"
                  max="8192"
                  step="256"
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="w-full px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <LoadingSpinner />
                    Generating...
                  </>
                ) : (
                  'Generate Code'
                )}
              </button>
            </div>
          </div>

          {/* Output Panel */}
          <div className="space-y-6">
            {result && !loading && (
              <>
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-slate-900 mb-4">
                    Generated Code
                  </h2>
                  <CodeOutput code={result.generated_code} language="python" />
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-slate-900 mb-4">
                    Execution Stats
                  </h2>
                  <ExecutionStats
                    tokens_used={result.tokens_used}
                    execution_time={result.execution_time}
                  />
                </div>

                <button
                  onClick={reset}
                  className="w-full px-6 py-2 bg-slate-200 text-slate-900 font-medium rounded-lg hover:bg-slate-300 transition-colors"
                >
                  Clear
                </button>
              </>
            )}

            {error && !loading && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-red-600">
                  <h3 className="font-semibold mb-2">Error</h3>
                  <p className="text-sm">
                    {(error.response?.data as any)?.detail ||
                      error.message ||
                      'An error occurred'}
                  </p>
                </div>
              </div>
            )}

            {loading && (
              <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center min-h-64">
                <div className="text-center">
                  <LoadingSpinner />
                  <p className="mt-4 text-slate-600">Generating code...</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
