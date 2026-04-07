import { useState } from 'react'
import { CodeEditor } from '@/components/CodeEditor'
import { CodeOutput } from '@/components/CodeOutput'
import { FileUpload } from '@/components/FileUpload'
import { ModelSelector } from '@/components/ModelSelector'
import { ExecutionStats } from '@/components/ExecutionStats'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useCodeAction } from '@/hooks/useCodeAction'
import type { Model, Framework, TestResponse } from '@/types/actions'

export const TestPage = () => {
  const [code, setCode] = useState('')
  const [framework, setFramework] = useState<Framework>('pytest')
  const [model, setModel] = useState<Model>('haiku')
  const [temperature, setTemperature] = useState(0.2)
  const [maxTokens, setMaxTokens] = useState(4096)
  const { data, loading, error, execute, reset } = useCodeAction()

  const result = data as TestResponse | null

  const handleGenerateTests = async () => {
    if (!code.trim()) {
      return
    }
    await execute({
      action: 'test',
      params: {
        code,
        framework,
        model,
        temperature,
        max_tokens: maxTokens,
      },
    })
  }

  const handleFileSelected = (content: string) => {
    setCode(content)
  }

  return (
    <div className="flex-1 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Generate Tests</h1>
        <p className="text-slate-600 mb-8">
          Automatically generate comprehensive unit tests for your code.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-3">
                  Code to Test
                </label>
                <CodeEditor
                  value={code}
                  onChange={setCode}
                  language="python"
                  placeholder="Paste your code here..."
                  height="h-40"
                />
              </div>

              <FileUpload onFileSelected={handleFileSelected} />

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-slate-900">
                    Test Framework
                  </label>
                  <select
                    value={framework}
                    onChange={(e) => setFramework(e.target.value as Framework)}
                    className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="pytest">pytest (Python)</option>
                    <option value="vitest">vitest (JavaScript)</option>
                    <option value="jest">jest (JavaScript)</option>
                  </select>
                </div>

                <ModelSelector value={model} onChange={setModel} />
              </div>

              <div className="grid grid-cols-2 gap-4">
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
              </div>

              <button
                onClick={handleGenerateTests}
                disabled={loading || !code.trim()}
                className="w-full px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <LoadingSpinner />
                    Generating Tests...
                  </>
                ) : (
                  'Generate Tests'
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
                    Generated Tests
                  </h2>
                  <CodeOutput
                    code={result.test_code}
                    language={framework === 'pytest' ? 'python' : 'typescript'}
                  />
                </div>

                {result.coverage_estimate && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-slate-900 mb-4">
                      Coverage Estimate
                    </h2>
                    <p className="text-slate-600 text-sm">
                      {result.coverage_estimate}
                    </p>
                  </div>
                )}

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
                  <p className="mt-4 text-slate-600">Generating tests...</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
