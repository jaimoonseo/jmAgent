import { useState } from 'react'
import { CodeEditor } from '@/components/CodeEditor'
import { FileUpload } from '@/components/FileUpload'
import { ModelSelector } from '@/components/ModelSelector'
import { ExecutionStats } from '@/components/ExecutionStats'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useCodeAction } from '@/hooks/useCodeAction'
import type { Model, Language, ExplainResponse } from '@/types/actions'

export const ExplainPage = () => {
  const [code, setCode] = useState('')
  const [focusArea, setFocusArea] = useState('')
  const [language, setLanguage] = useState<Language>('en')
  const [model, setModel] = useState<Model>('haiku')
  const { data, loading, error, execute, reset } = useCodeAction()

  const result = data as ExplainResponse | null

  const handleExplain = async () => {
    if (!code.trim()) {
      return
    }
    await execute({
      action: 'explain',
      params: {
        code,
        focus_area: focusArea || undefined,
        language,
        model,
      },
    })
  }

  const handleFileSelected = (content: string) => {
    setCode(content)
  }

  return (
    <div className="flex-1 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Explain Code</h1>
        <p className="text-slate-600 mb-8">
          Get detailed explanations of any code snippet.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-3">
                  Code to Explain
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

              <div>
                <label className="block text-sm font-medium text-slate-900 mb-3">
                  Focus Area (Optional)
                </label>
                <textarea
                  value={focusArea}
                  onChange={(e) => setFocusArea(e.target.value)}
                  placeholder="e.g., Explain how the caching works, What does the decorator do..."
                  className="w-full h-20 p-4 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-slate-900">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value as Language)}
                    className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="en">English</option>
                    <option value="ko">Korean (한국어)</option>
                  </select>
                </div>

                <ModelSelector value={model} onChange={setModel} />
              </div>

              <button
                onClick={handleExplain}
                disabled={loading || !code.trim()}
                className="w-full px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <LoadingSpinner />
                    Explaining...
                  </>
                ) : (
                  'Explain Code'
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
                    Explanation
                  </h2>
                  <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">
                    {result.explanation}
                  </p>
                </div>

                {result.key_concepts.length > 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-slate-900 mb-4">
                      Key Concepts
                    </h2>
                    <div className="flex flex-wrap gap-2">
                      {result.key_concepts.map((concept, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-primary-100 text-primary-700 text-sm rounded-full"
                        >
                          {concept}
                        </span>
                      ))}
                    </div>
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
                  <p className="mt-4 text-slate-600">Analyzing code...</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
