import { useRef, useEffect, useState } from 'react'
import type { ChatMessage, Model } from '@/types/actions'

interface WorkspaceCenterPanelProps {
  centerTab: 'chat' | 'workflow' | 'batch'
  setCenterTab: (tab: 'chat' | 'workflow' | 'batch') => void

  // Chat props
  messages: ChatMessage[]
  chatInput: string
  chatLoading: boolean
  model: Model
  contextFiles: Array<{ path: string; content: string }>
  isStreaming: boolean
  streamProgress: string[]
  streamStats: { executionTime: number; tokensUsed: { input: number; output: number; total: number } } | null
  selectedSkills: Array<{ id: string; name: string }>
  selectedFiles: Set<string>

  // Workflow props
  workflowSteps: Array<{
    id: string
    instruction: string
    status: 'pending' | 'running' | 'done' | 'error'
    result?: string
    contextFiles?: Array<{ path: string; content: string }>
    skills?: Array<{ id: string; name: string }>
    createdFiles?: string[]
    dependsOn?: string[]
    streamingContent?: string
    excludeBatchTarget?: boolean
  }>
  newStepInput: string
  isWorkflowRunning: boolean

  onModelChange: (model: Model) => void
  onNewChat: () => void
  onChatInputChange: (value: string) => void
  onSendMessage: () => void
  onKeyDown: (e: React.KeyboardEvent) => void
  onCompositionStart?: () => void
  onCompositionEnd?: () => void
  onAddWorkflowStep: () => void
  onRemoveWorkflowStep: (stepId: string) => void
  onRunWorkflow: () => void
  onNewStepInputChange: (value: string) => void
  onUpdateWorkflowStep?: (stepId: string, instruction: string) => void
  onRemoveStepContext?: (stepId: string, filePath: string) => void
  onRemoveStepSkill?: (stepId: string, skillId: string) => void
  onToggleStepDependency?: (stepId: string, depStepId: string) => void
  onRerunStep?: (stepId: string) => void

  // Template props
  workflowTemplates?: Array<{ id: string; name: string; steps: any[] }>
  onSaveWorkflowTemplate?: (name: string) => void
  onLoadWorkflowTemplate?: (templateId: string) => void
  onDeleteWorkflowTemplate?: (templateId: string) => void

  // Batch props
  projectFiles?: Array<{ name: string; path: string; type: 'file' | 'directory' }>
  batchAllFiles?: Array<{ path: string; name: string }>
  batchFolder?: string
  batchFileFilter?: string
  batchFiles?: Array<{ path: string; name: string }>
  batchSelectedFiles?: Set<string>
  batchTemplateId?: string
  isBatchRunning?: boolean
  batchProgress?: Array<{ file: string; status: string; currentStep?: number; totalSteps?: number; error?: string }>
  batchConcurrency?: number
  onBatchFolderChange?: (folder: string) => void
  onBatchFileFilterChange?: (filter: string) => void
  onBatchLoadFolder?: () => void
  onToggleBatchFile?: (path: string) => void
  onToggleAllBatchFiles?: () => void
  onBatchTemplateChange?: (templateId: string) => void
  onBatchConcurrencyChange?: (n: number) => void
  onRunBatch?: () => void
}

export const WorkspaceCenterPanel = ({
  centerTab,
  setCenterTab,
  messages,
  chatInput,
  chatLoading,
  model,
  contextFiles,
  isStreaming,
  streamProgress,
  streamStats,
  selectedSkills,
  selectedFiles,
  workflowSteps,
  newStepInput,
  isWorkflowRunning,
  onModelChange,
  onNewChat,
  onChatInputChange,
  onSendMessage,
  onKeyDown,
  onCompositionStart,
  onCompositionEnd,
  onAddWorkflowStep,
  onRemoveWorkflowStep,
  onRunWorkflow,
  onNewStepInputChange,
  onUpdateWorkflowStep,
  onRemoveStepContext,
  onRemoveStepSkill,
  onToggleStepDependency,
  onRerunStep,
  // Template props
  workflowTemplates,
  onSaveWorkflowTemplate,
  onLoadWorkflowTemplate,
  onDeleteWorkflowTemplate,
  // Batch props
  projectFiles,
  batchAllFiles,
  batchFolder,
  batchFileFilter,
  batchFiles,
  batchSelectedFiles,
  batchTemplateId,
  isBatchRunning,
  batchProgress,
  batchConcurrency,
  onBatchFolderChange,
  onBatchFileFilterChange,
  onBatchLoadFolder,
  onToggleBatchFile,
  onToggleAllBatchFiles,
  onBatchTemplateChange,
  onBatchConcurrencyChange,
  onRunBatch,
}: WorkspaceCenterPanelProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const streamingPreRef = useRef<HTMLPreElement>(null)
  const [editingStepId, setEditingStepId] = useState<string | null>(null)
  const [editingStepInstruction, setEditingStepInstruction] = useState('')
  const [templateNameInput, setTemplateNameInput] = useState('')
  const [showTemplateSave, setShowTemplateSave] = useState(false)

  // 스트리밍 내용 변경 시 자동 스크롤
  const runningStep = workflowSteps.find((s) => s.status === 'running')
  useEffect(() => {
    if (streamingPreRef.current) {
      streamingPreRef.current.scrollTop = streamingPreRef.current.scrollHeight
    }
  }, [runningStep?.streamingContent])

  useEffect(() => {
    // Auto-scroll when messages or progress updates
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 0)
  }, [messages, streamProgress, isStreaming])

  return (
    <div className="flex-1 flex flex-col bg-white min-w-0">
      {/* Tabs */}
      <div className="flex border-b flex-shrink-0">
        <button
          onClick={() => setCenterTab('chat')}
          className={`px-4 py-2 font-medium text-sm ${
            centerTab === 'chat'
              ? 'border-b-2 border-primary-600 text-primary-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Chat
        </button>
        <button
          onClick={() => setCenterTab('workflow')}
          className={`px-4 py-2 font-medium text-sm ${
            centerTab === 'workflow'
              ? 'border-b-2 border-primary-600 text-primary-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Workflow
        </button>
        <button
          onClick={() => setCenterTab('batch')}
          className={`px-4 py-2 font-medium text-sm ${
            centerTab === 'batch'
              ? 'border-b-2 border-primary-600 text-primary-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Batch
        </button>
      </div>

      {/* Chat Tab */}
      {centerTab === 'chat' && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* Model selector */}
          <div className="p-3 border-b flex-shrink-0 flex gap-3 items-center">
            <label className="text-sm font-medium text-slate-700">Model:</label>
            <select
              value={model}
              onChange={(e) => onModelChange(e.target.value as Model)}
              disabled={messages.length > 0}
              className="px-3 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100"
            >
              <option value="haiku">Haiku 4.5 (Fast)</option>
              <option value="sonnet">Sonnet 4.6 (Balanced)</option>
              <option value="opus">Opus 4.6 (Quality)</option>
            </select>
            <button
              onClick={onNewChat}
              className="ml-auto px-3 py-1 bg-slate-200 hover:bg-slate-300 rounded text-sm font-medium"
            >
              New Chat
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !chatLoading && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-4xl mb-3">💬</div>
                  <p className="text-slate-600">Start a conversation</p>
                  <p className="text-xs text-slate-500">
                    {contextFiles.length > 0
                      ? `${contextFiles.length} file(s) in context`
                      : 'Add files to context first'}
                  </p>
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}-${msg.content.length}`}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-md px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-slate-100 text-slate-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}

            {(isStreaming || streamProgress.length > 0) && (
              <div className={`p-3 rounded border font-mono text-xs space-y-1 ${
                isStreaming
                  ? 'bg-slate-900 text-green-400 border-green-500'
                  : 'bg-green-50 text-green-900 border-green-300'
              }`}>
                {streamProgress.map((line, idx) => (
                  <div key={idx}>{line}</div>
                ))}
                {streamStats && !isStreaming && (
                  <>
                    <div>✅ TASK COMPLETED!</div>
                    <div>⏱️ {streamStats.executionTime.toFixed(2)}s</div>
                    <div>📊 Tokens: {streamStats.tokensUsed.total}</div>
                  </>
                )}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t flex-shrink-0 space-y-2">
            {/* Selected Tags */}
            {(selectedSkills.length > 0 || selectedFiles.size > 0) && (
              <div className="flex flex-wrap gap-2">
                {selectedSkills.map((skill) => (
                  <span key={skill.id} className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                    ✨ {skill.name}
                  </span>
                ))}
                {Array.from(selectedFiles).map((filePath) => (
                  <span key={filePath} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                    📄 {filePath.split('/').pop()}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <textarea
                value={chatInput}
                onChange={(e) => onChatInputChange(e.target.value)}
                onKeyDown={onKeyDown}
                onCompositionStart={onCompositionStart}
                onCompositionEnd={onCompositionEnd}
                placeholder="Type message... (Shift+Enter for new line)"
                disabled={chatLoading}
                className="flex-1 p-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none max-h-24 disabled:bg-slate-100"
                rows={2}
              />
              <button
                onClick={onSendMessage}
                disabled={chatLoading || !chatInput.trim()}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded font-medium text-sm disabled:bg-slate-400 flex-shrink-0 self-end"
              >
                {chatLoading ? 'Sending' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Tab */}
      {centerTab === 'workflow' && (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* Workflow Steps */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {workflowSteps.length === 0 ? (
                <div className="flex items-center justify-center h-full text-slate-400">
                  <div className="text-center">
                    <div className="text-4xl mb-3">⚙️</div>
                    <p className="text-sm">No workflow steps yet</p>
                    <p className="text-xs text-slate-500">Add a step below to get started</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {workflowSteps.map((step, idx) => {
                    const isEditing = editingStepId === step.id
                    return (
                      <div
                        key={step.id}
                        className={`p-3 rounded border ${
                          step.status === 'done'
                            ? 'bg-green-50 border-green-300'
                            : step.status === 'running'
                            ? 'bg-blue-50 border-blue-300'
                            : step.status === 'error'
                            ? 'bg-red-50 border-red-300'
                            : 'bg-slate-50 border-slate-300'
                        }`}
                      >
                        {!isEditing ? (
                          <div className="flex items-start gap-2">
                            <span className="font-semibold text-sm text-slate-600 flex-shrink-0 w-6">{idx + 1}.</span>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-900 line-clamp-2">{step.instruction}</p>

                              {/* 단계별 컨텍스트 파일 배지 */}
                              {step.contextFiles && step.contextFiles.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {step.contextFiles.map((f) => (
                                    <span
                                      key={f.path}
                                      className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                                      title={f.path}
                                    >
                                      📄 {f.path.split('/').pop()}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {/* 단계별 스킬 배지 */}
                              {step.skills && step.skills.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {step.skills.map((s) => (
                                    <span key={s.id} className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                                      ✨ {s.name}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {/* 의존성 배지 */}
                              {step.dependsOn && step.dependsOn.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {step.dependsOn.map((depId) => {
                                    const depIdx = workflowSteps.findIndex((s) => s.id === depId)
                                    if (depIdx < 0) return null
                                    return (
                                      <span key={depId} className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">
                                        ← Step {depIdx + 1}
                                      </span>
                                    )
                                  })}
                                </div>
                              )}

                              {/* 상태 표시 */}
                              {step.status === 'done' && <p className="text-xs text-green-600 mt-1">✅ Complete</p>}
                              {step.status === 'running' && (
                                <div className="mt-1">
                                  <p className="text-xs text-blue-600">▶️ Running...</p>
                                  {step.streamingContent && (
                                    <pre ref={streamingPreRef} className="mt-1 p-2 bg-slate-900 text-green-400 text-xs rounded max-h-32 overflow-y-auto whitespace-pre-wrap break-words font-mono">
                                      {step.streamingContent}
                                    </pre>
                                  )}
                                </div>
                              )}
                              {step.status === 'error' && <p className="text-xs text-red-600 mt-1">❌ Failed{step.result ? `: ${step.result}` : ''}</p>}
                            </div>
                            <div className="flex gap-1 flex-shrink-0">
                              {(step.status === 'done' || step.status === 'error') && (
                                <button
                                  onClick={() => onRerunStep?.(step.id)}
                                  disabled={isWorkflowRunning}
                                  className="px-2 py-1 bg-orange-500 hover:bg-orange-600 text-white rounded text-xs disabled:bg-slate-400"
                                  title="Re-run this step"
                                >
                                  Re-run
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  setEditingStepId(step.id)
                                  setEditingStepInstruction(step.instruction)
                                }}
                                disabled={isWorkflowRunning}
                                className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs disabled:bg-slate-400"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => onRemoveWorkflowStep(step.id)}
                                disabled={isWorkflowRunning}
                                className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs disabled:bg-slate-400"
                              >
                                Remove
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <p className="text-sm font-semibold text-slate-900">Step {idx + 1} - Edit</p>
                            <textarea
                              value={editingStepInstruction}
                              onChange={(e) => setEditingStepInstruction(e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-blue-300 rounded font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                              rows={3}
                            />

                            {/* 컨텍스트 파일 편집 */}
                            {step.contextFiles && step.contextFiles.length > 0 && (
                              <div>
                                <p className="text-xs text-slate-500 mb-1">Context Files:</p>
                                <div className="flex flex-wrap gap-1">
                                  {step.contextFiles.map((f) => (
                                    <span
                                      key={f.path}
                                      className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                                    >
                                      {f.path.split('/').pop()}
                                      <button
                                        onClick={() => onRemoveStepContext?.(step.id, f.path)}
                                        className="text-blue-400 hover:text-red-600 font-bold ml-0.5"
                                        title={`Remove ${f.path}`}
                                      >
                                        x
                                      </button>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 스킬 편집 */}
                            {step.skills && step.skills.length > 0 && (
                              <div>
                                <p className="text-xs text-slate-500 mb-1">Skills:</p>
                                <div className="flex flex-wrap gap-1">
                                  {step.skills.map((s) => (
                                    <span
                                      key={s.id}
                                      className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium"
                                    >
                                      {s.name}
                                      <button
                                        onClick={() => onRemoveStepSkill?.(step.id, s.id)}
                                        className="text-purple-400 hover:text-red-600 font-bold ml-0.5"
                                        title={`Remove ${s.name}`}
                                      >
                                        x
                                      </button>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 이전 step 의존성 선택 (실행 시 해당 step의 결과물이 컨텍스트에 자동 주입) */}
                            {idx > 0 && (
                              <div>
                                <p className="text-xs text-slate-500 mb-1">Include output from:</p>
                                <div className="flex flex-wrap gap-1">
                                  {workflowSteps.slice(0, idx).map((prevStep, prevIdx) => {
                                    const isDepended = step.dependsOn?.includes(prevStep.id)
                                    return (
                                      <button
                                        key={prevStep.id}
                                        onClick={() => onToggleStepDependency?.(step.id, prevStep.id)}
                                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                                          isDepended
                                            ? 'bg-green-600 text-white'
                                            : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                                        }`}
                                        title={prevStep.instruction}
                                      >
                                        Step {prevIdx + 1}
                                      </button>
                                    )
                                  })}
                                </div>
                              </div>
                            )}

                            <div className="flex gap-2">
                              <button
                                onClick={() => {
                                  if (onUpdateWorkflowStep) {
                                    onUpdateWorkflowStep(step.id, editingStepInstruction)
                                  }
                                  setEditingStepId(null)
                                }}
                                className="flex-1 px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-medium"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => setEditingStepId(null)}
                                className="flex-1 px-2 py-1 bg-slate-400 hover:bg-slate-500 text-white rounded text-xs font-medium"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}

              {isStreaming && streamProgress.length > 0 && (
                <div className="bg-slate-900 text-green-400 p-3 rounded border border-green-500 font-mono text-xs space-y-1">
                  {streamProgress.map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
                </div>
              )}

              {!isStreaming && streamStats && (
                <div className="bg-green-50 text-green-900 p-3 rounded border border-green-300 font-mono text-xs space-y-1">
                  <div>✅ WORKFLOW COMPLETED!</div>
                  <div>📊 {workflowSteps.length} step(s) executed</div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-3 border-t flex-shrink-0 space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newStepInput}
                  onChange={(e) => onNewStepInputChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      onAddWorkflowStep()
                    }
                  }}
                  placeholder="Enter workflow step instruction..."
                  disabled={isWorkflowRunning}
                  className="flex-1 p-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100"
                />
                <button
                  onClick={onAddWorkflowStep}
                  disabled={isWorkflowRunning || !newStepInput.trim()}
                  className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-sm font-medium rounded disabled:bg-slate-400 flex-shrink-0"
                >
                  + Add
                </button>
              </div>

              {workflowSteps.length > 0 && (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <select
                      value={model}
                      onChange={(e) => onModelChange(e.target.value as Model)}
                      disabled={isWorkflowRunning}
                      className="px-2 py-2 text-sm border border-slate-300 rounded bg-white disabled:bg-slate-100"
                    >
                      <option value="haiku">Haiku</option>
                      <option value="sonnet">Sonnet</option>
                      <option value="opus">Opus</option>
                    </select>
                    <button
                      onClick={onRunWorkflow}
                      disabled={isWorkflowRunning}
                      className="flex-1 px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded text-sm font-medium disabled:bg-slate-400"
                    >
                      {isWorkflowRunning ? '▶️ Running...' : '▶️ Run Workflow'}
                    </button>
                  </div>

                  {/* Template Save/Load */}
                  <div className="flex gap-2 items-center">
                    {!showTemplateSave ? (
                      <button
                        onClick={() => setShowTemplateSave(true)}
                        disabled={isWorkflowRunning}
                        className="px-2 py-1 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded text-xs font-medium disabled:opacity-50"
                      >
                        Save as Template
                      </button>
                    ) : (
                      <>
                        <input
                          type="text"
                          value={templateNameInput}
                          onChange={(e) => setTemplateNameInput(e.target.value)}
                          placeholder="Template name..."
                          className="flex-1 px-2 py-1 text-xs border rounded focus:outline-none focus:ring-1 focus:ring-amber-500"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && templateNameInput.trim()) {
                              onSaveWorkflowTemplate?.(templateNameInput)
                              setTemplateNameInput('')
                              setShowTemplateSave(false)
                            }
                          }}
                        />
                        <button
                          onClick={() => {
                            if (templateNameInput.trim()) {
                              onSaveWorkflowTemplate?.(templateNameInput)
                              setTemplateNameInput('')
                              setShowTemplateSave(false)
                            }
                          }}
                          className="px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded text-xs"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => { setShowTemplateSave(false); setTemplateNameInput('') }}
                          className="px-2 py-1 bg-slate-300 hover:bg-slate-400 text-slate-700 rounded text-xs"
                        >
                          Cancel
                        </button>
                      </>
                    )}

                    {workflowTemplates && workflowTemplates.length > 0 && (
                      <select
                        onChange={(e) => {
                          if (e.target.value) onLoadWorkflowTemplate?.(e.target.value)
                          e.target.value = ''
                        }}
                        defaultValue=""
                        className="px-2 py-1 text-xs border rounded bg-white"
                      >
                        <option value="" disabled>Load Template...</option>
                        {workflowTemplates.map((t) => (
                          <option key={t.id} value={t.id}>{t.name} ({t.steps.length} steps)</option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Batch Tab */}
      {centerTab === 'batch' && (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Folder Selection */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">Target Folder (relative path)</h3>
              <div className="flex gap-2">
                {(() => {
                  const dirs = projectFiles?.filter((f) => f.type === 'directory') || []
                  return dirs.length > 0 ? (
                    <select
                      value={batchFolder || ''}
                      onChange={(e) => onBatchFolderChange?.(e.target.value)}
                      disabled={isBatchRunning}
                      className="flex-1 px-2 py-1.5 text-sm border border-slate-300 rounded bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100"
                    >
                      <option value="">Select folder...</option>
                      {dirs.map((d) => (
                        <option key={d.path} value={d.path}>{d.path}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={batchFolder || ''}
                      onChange={(e) => onBatchFolderChange?.(e.target.value)}
                      placeholder="e.g. mts/screens"
                      disabled={isBatchRunning}
                      className="flex-1 px-2 py-1.5 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100"
                    />
                  )
                })()}
                <button
                  onClick={onBatchLoadFolder}
                  disabled={isBatchRunning || !batchFolder}
                  className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded text-sm font-medium disabled:bg-slate-400"
                >
                  Load
                </button>
              </div>
            </div>

            {/* File Filter */}
            {(batchAllFiles?.length || 0) > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-700">
                    Files ({batchSelectedFiles?.size || 0}/{batchAllFiles?.length || 0} selected)
                    {batchFileFilter && batchFiles && batchAllFiles && batchFiles.length !== batchAllFiles.length && (
                      <span className="text-slate-400 font-normal ml-1">(showing {batchFiles.length})</span>
                    )}
                  </h3>
                  <button
                    onClick={onToggleAllBatchFiles}
                    disabled={isBatchRunning}
                    className="text-xs text-primary-600 hover:text-primary-800 font-medium disabled:opacity-50"
                  >
                    {batchFiles?.every((f) => batchSelectedFiles?.has(f.path)) ? 'Deselect All' : 'Select All'}
                  </button>
                </div>

                <input
                  type="text"
                  value={batchFileFilter || ''}
                  onChange={(e) => onBatchFileFilterChange?.(e.target.value)}
                  placeholder="Filter (regex)... e.g. \.xmf$"
                  disabled={isBatchRunning}
                  className="w-full px-2 py-1.5 text-sm border border-slate-300 rounded font-mono focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-slate-100"
                />

                <div className="max-h-48 overflow-y-auto border rounded divide-y">
                  {batchFiles?.map((file) => (
                    <label
                      key={file.path}
                      className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-50 cursor-pointer text-xs"
                    >
                      <input
                        type="checkbox"
                        checked={batchSelectedFiles?.has(file.path) || false}
                        onChange={() => onToggleBatchFile?.(file.path)}
                        disabled={isBatchRunning}
                        className="w-3 h-3"
                      />
                      <span className="text-slate-700 font-mono truncate" title={file.path}>{file.path}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Workflow Template Selection */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">Workflow Template</h3>
              {workflowTemplates && workflowTemplates.length > 0 ? (
                <div className="space-y-1">
                  {workflowTemplates.map((t) => (
                    <div
                      key={t.id}
                      className={`flex items-center justify-between p-2 rounded border cursor-pointer text-xs ${
                        batchTemplateId === t.id
                          ? 'bg-primary-50 border-primary-400'
                          : 'bg-white border-slate-200 hover:border-slate-400'
                      }`}
                      onClick={() => onBatchTemplateChange?.(t.id)}
                    >
                      <div>
                        <p className="font-medium text-slate-900">{t.name}</p>
                        <p className="text-slate-500">{t.steps.length} steps</p>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={(e) => { e.stopPropagation(); onDeleteWorkflowTemplate?.(t.id) }}
                          className="px-1.5 py-0.5 text-red-500 hover:bg-red-50 rounded"
                          title="Delete template"
                        >
                          x
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No templates. Save a workflow as template first (Workflow tab).</p>
              )}
            </div>

            {/* Concurrency */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-700">Parallel:</label>
              <select
                value={batchConcurrency || 1}
                onChange={(e) => onBatchConcurrencyChange?.(parseInt(e.target.value))}
                disabled={isBatchRunning}
                className="px-2 py-1 text-sm border rounded bg-white disabled:bg-slate-100"
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            {/* Batch Progress */}
            {batchProgress && batchProgress.length > 0 && (
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-700">Progress</h3>
                <div className="max-h-64 overflow-y-auto border rounded divide-y">
                  {batchProgress.map((p, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between px-2 py-1.5 text-xs ${
                        p.status === 'done' ? 'bg-green-50' :
                        p.status === 'running' ? 'bg-blue-50' :
                        p.status === 'error' ? 'bg-red-50' : 'bg-white'
                      }`}
                    >
                      <span className="font-mono truncate flex-1" title={p.file}>
                        {p.file.split('/').pop()}
                      </span>
                      <span className="flex-shrink-0 ml-2">
                        {p.status === 'pending' && <span className="text-slate-400">Waiting</span>}
                        {p.status === 'running' && (
                          <span className="text-blue-600">Step {p.currentStep}/{p.totalSteps}</span>
                        )}
                        {p.status === 'done' && <span className="text-green-600">Done</span>}
                        {p.status === 'error' && (
                          <span className="text-red-600" title={p.error}>Failed</span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
                {!isBatchRunning && batchProgress.length > 0 && (
                  <div className="text-xs text-slate-500">
                    {batchProgress.filter((p) => p.status === 'done').length}/{batchProgress.length} completed
                    {batchProgress.some((p) => p.status === 'error') &&
                      `, ${batchProgress.filter((p) => p.status === 'error').length} failed`
                    }
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Run Batch Button */}
          <div className="p-3 border-t flex-shrink-0">
            <div className="flex gap-2">
              <select
                value={model}
                onChange={(e) => onModelChange(e.target.value as Model)}
                disabled={isBatchRunning}
                className="px-2 py-2 text-sm border border-slate-300 rounded bg-white disabled:bg-slate-100"
              >
                <option value="haiku">Haiku</option>
                <option value="sonnet">Sonnet</option>
                <option value="opus">Opus</option>
              </select>
              <button
                onClick={onRunBatch}
                disabled={isBatchRunning || !batchTemplateId || (batchSelectedFiles?.size || 0) === 0}
                className="flex-1 px-3 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded text-sm font-medium disabled:bg-slate-400"
              >
                {isBatchRunning ? 'Running Batch...' : `Run Batch (${batchSelectedFiles?.size || 0} files)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
