interface CodeBlock {
  language: string
  code: string
  suggestedFilename: string
}

interface WorkspaceRightPanelProps {
  rightTab: 'output' | 'agentmd' | 'file'
  setRightTab: (tab: 'output' | 'agentmd' | 'file') => void

  outputBlocks: CodeBlock[]
  agentMdContent: string
  viewingFile: { path: string; content: string } | null
  isEditingMode: boolean
  agentMdSaving: boolean
  projectRoot: string

  onCopyToClipboard: (block?: CodeBlock) => void
  onSaveAllOutput: () => void
  onSaveBlock: (block: CodeBlock, index: number) => void
  onSaveAgentMd: () => void
  onAgentMdChange: (value: string) => void
  onStartEditFile: () => void
  onSaveEditedFile: () => void
  onCancelEditFile: () => void
}

export const WorkspaceRightPanel = ({
  rightTab,
  setRightTab,
  outputBlocks,
  agentMdContent,
  viewingFile,
  isEditingMode,
  agentMdSaving,
  projectRoot,
  onCopyToClipboard,
  onSaveAllOutput,
  onSaveBlock,
  onSaveAgentMd,
  onAgentMdChange,
  onStartEditFile,
  onSaveEditedFile,
  onCancelEditFile,
}: WorkspaceRightPanelProps) => {
  return (
    <div className="w-96 flex-shrink-0 border-l bg-white flex flex-col">
      {/* Tabs */}
      <div className="flex border-b flex-shrink-0">
        <button
          onClick={() => setRightTab('output')}
          className={`px-4 py-2 font-medium text-sm ${
            rightTab === 'output'
              ? 'border-b-2 border-primary-600 text-primary-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Output
        </button>
        <button
          onClick={() => setRightTab('agentmd')}
          className={`px-4 py-2 font-medium text-sm ${
            rightTab === 'agentmd'
              ? 'border-b-2 border-primary-600 text-primary-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          agent.md
        </button>
        <button
          onClick={() => setRightTab('file')}
          className={`px-4 py-2 font-medium text-sm ${
            rightTab === 'file'
              ? 'border-b-2 border-primary-600 text-primary-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          File
        </button>
      </div>

      {/* Output Tab */}
      {rightTab === 'output' && (
        <div className="flex-1 flex flex-col min-h-0 p-4">
          {outputBlocks.length > 0 ? (
            <>
              {/* Header */}
              <div className="mb-3 flex-shrink-0 pb-2 border-b">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-slate-900">Generated ({outputBlocks.length} file{outputBlocks.length !== 1 ? 's' : ''})</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => onCopyToClipboard()}
                      className="px-3 py-1 bg-slate-200 hover:bg-slate-300 rounded text-xs font-medium"
                    >
                      📋 Copy All
                    </button>
                    <button
                      onClick={onSaveAllOutput}
                      disabled={!projectRoot}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium disabled:bg-slate-400"
                    >
                      💾 Save All
                    </button>
                  </div>
                </div>
              </div>

              {/* Code Blocks */}
              <div className="flex-1 overflow-y-auto space-y-3">
                {outputBlocks.map((block, idx) => (
                  <div key={idx} className="border border-slate-200 rounded overflow-hidden">
                    {/* Block Header */}
                    <div className="bg-slate-100 px-3 py-2 flex justify-between items-center text-xs">
                      <div>
                        <div className="font-mono font-semibold text-slate-900">{block.suggestedFilename}</div>
                        <div className="text-slate-500">{block.language} • {block.code.length} bytes</div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => onCopyToClipboard(block)}
                          className="px-2 py-1 bg-slate-200 hover:bg-slate-300 rounded text-xs font-medium"
                        >
                          📋
                        </button>
                        <button
                          onClick={() => onSaveBlock(block, idx)}
                          disabled={!projectRoot}
                          className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium disabled:bg-slate-400"
                        >
                          💾
                        </button>
                      </div>
                    </div>

                    {/* Code */}
                    <pre className="max-h-32 bg-slate-900 text-green-400 p-2 font-mono text-xs overflow-auto">
                      {block.code.slice(0, 500)}
                      {block.code.length > 500 && '\n... (truncated for display)'}
                    </pre>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              <p className="text-sm">Generated code will appear here</p>
            </div>
          )}
        </div>
      )}

      {/* agent.md Tab */}
      {rightTab === 'agentmd' && (
        <div className="flex-1 flex flex-col min-h-0 p-4">
          <div className="mb-3 flex-shrink-0">
            <div className="flex justify-between items-start">
              <span className="font-semibold text-slate-900">agent.md</span>
              <button
                onClick={onSaveAgentMd}
                disabled={!projectRoot || agentMdSaving}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium disabled:bg-slate-400"
              >
                {agentMdSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
          <textarea
            value={agentMdContent}
            onChange={(e) => onAgentMdChange(e.target.value)}
            className="flex-1 p-3 text-sm border border-slate-300 rounded font-mono focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            placeholder={projectRoot ? 'Edit agent.md...' : 'Open a project to edit'}
            disabled={!projectRoot}
          />
        </div>
      )}

      {/* File Tab */}
      {rightTab === 'file' && (
        <div className="flex-1 flex flex-col min-h-0 p-4">
          {viewingFile ? (
            <>
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-slate-600 truncate flex-1">{viewingFile.path}</p>
                <div className="flex gap-2 flex-shrink-0">
                  {!isEditingMode ? (
                    <button
                      onClick={onStartEditFile}
                      className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium"
                    >
                      ✏️ Edit
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={onSaveEditedFile}
                        className="px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-medium"
                      >
                        💾 Save
                      </button>
                      <button
                        onClick={onCancelEditFile}
                        className="px-2 py-1 bg-slate-600 hover:bg-slate-700 text-white rounded text-xs font-medium"
                      >
                        ✕ Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>

              {isEditingMode ? (
                <textarea
                  value={viewingFile.content}
                  className="flex-1 p-3 border border-blue-400 rounded font-mono text-xs overflow-auto focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  disabled
                />
              ) : (
                <pre className="flex-1 bg-slate-50 p-3 rounded font-mono text-xs overflow-auto border">
                  {viewingFile.content}
                </pre>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              <p className="text-sm">Click on a file to view</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
