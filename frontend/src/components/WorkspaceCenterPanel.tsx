import { useRef, useEffect } from 'react'
import type { ChatMessage, Model } from '@/types/actions'

interface WorkspaceCenterPanelProps {
  centerTab: 'chat' | 'workflow'
  setCenterTab: (tab: 'chat' | 'workflow') => void

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
  workflowSteps: Array<{ id: string; instruction: string; status: 'pending' | 'running' | 'done' | 'error'; result?: string }>
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
}: WorkspaceCenterPanelProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

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
                  {workflowSteps.map((step, idx) => (
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
                      <div className="flex items-start gap-2">
                        <span className="font-semibold text-sm text-slate-600 flex-shrink-0 w-6">{idx + 1}.</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 line-clamp-2">{step.instruction}</p>
                          {step.status === 'done' && <p className="text-xs text-green-600 mt-1">✅ Complete</p>}
                          {step.status === 'running' && <p className="text-xs text-blue-600 mt-1">▶️ Running...</p>}
                          {step.status === 'error' && <p className="text-xs text-red-600 mt-1">❌ Failed</p>}
                        </div>
                        <button
                          onClick={() => onRemoveWorkflowStep(step.id)}
                          disabled={isWorkflowRunning}
                          className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs flex-shrink-0 disabled:bg-slate-400"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
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
                <button
                  onClick={onRunWorkflow}
                  disabled={isWorkflowRunning}
                  className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded text-sm font-medium disabled:bg-slate-400"
                >
                  {isWorkflowRunning ? '▶️ Running...' : '▶️ Run Workflow'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
