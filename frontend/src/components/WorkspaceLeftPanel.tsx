import { useState, useEffect } from 'react'
import { filesApi } from '@/api/endpoints'
import { FileInfo } from '@/types/files'
import toast from 'react-hot-toast'

interface WorkspaceLeftPanelProps {
  projectRoot: string
  files: FileInfo[]
  contextFiles: Array<{ path: string; content: string }>
  projectPathInput: string
  agentMdSaving: boolean
  messages: any[]
  selectedSkills: Array<{ id: string; name: string }>
  selectedFiles: Set<string>
  allSkills: Array<{ id: string; name: string; content: string; enabled: boolean; createdAt: number }>

  onOpenProject: (path: string) => void
  onProjectPathChange: (value: string) => void
  onRefreshFileTree: () => void
  onRemoveContext: (path: string) => void
  onFileView: (file: FileInfo) => void
  onAddToContext: (file: FileInfo) => void
  onInitAgentMd: () => void
  onSaveAgentMd: () => void
  onRestoreSession: (session: any) => void
  onSelectSkill: (skill: { id: string; name: string }, selected: boolean) => void
  onSelectFile: (filePath: string, selected: boolean) => void
  onAddSelectedFilesToContext: () => void
  onAddSkill: (skillName: string, skillContent: string) => void
  onDeleteSkill: (skillId: string) => void
}

const WORKSPACE_SESSIONS_KEY = 'jmAgent:workspace:sessions'

export const WorkspaceLeftPanel = ({
  projectRoot,
  files,
  contextFiles,
  projectPathInput,
  agentMdSaving,
  messages,
  selectedSkills,
  selectedFiles,
  allSkills,
  onOpenProject,
  onProjectPathChange,
  onRefreshFileTree,
  onRemoveContext,
  onFileView,
  onAddToContext,
  onInitAgentMd,
  onSaveAgentMd,
  onRestoreSession,
  onSelectSkill,
  onSelectFile,
  onAddSelectedFilesToContext,
  onAddSkill,
  onDeleteSkill,
}: WorkspaceLeftPanelProps) => {
  const [showInput, setShowInput] = useState(false)
  const [showSkillManager, setShowSkillManager] = useState(false)
  const [showSessions, setShowSessions] = useState(false)
  const [newSkillName, setNewSkillName] = useState('')
  const [newSkillContent, setNewSkillContent] = useState('')
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())
  const [dirChildren, setDirChildren] = useState<Record<string, FileInfo[]>>({})
  const [savedSessions, setSavedSessions] = useState<any[]>([])
  const [sessionName, setSessionName] = useState('')

  // Load sessions on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(WORKSPACE_SESSIONS_KEY)
      if (saved) {
        setSavedSessions(JSON.parse(saved))
      }
    } catch {
      // ignore
    }
  }, [])

  const handleSaveCurrentSession = () => {
    const name = sessionName.trim()
    if (!name) {
      toast.error('Please enter a session name')
      return
    }
    if (!projectRoot) {
      toast.error('Please open a project first')
      return
    }

    const session = {
      id: Date.now().toString(),
      name,
      projectRoot,
      timestamp: Date.now(),
      contextFiles: contextFiles.map((f) => ({ path: f.path })),
      messages: messages, // Save entire conversation history
      messageCount: messages.length,
    }

    const updated = [...savedSessions, session]
    setSavedSessions(updated)
    localStorage.setItem(WORKSPACE_SESSIONS_KEY, JSON.stringify(updated))
    setSessionName('')
    toast.success(`✅ Saved session: ${name}`)
  }

  const handleDeleteSession = (id: string) => {
    const updated = savedSessions.filter((s) => s.id !== id)
    setSavedSessions(updated)
    localStorage.setItem(WORKSPACE_SESSIONS_KEY, JSON.stringify(updated))
    toast.success('Session deleted')
  }

  const handleRestoreSession = (session: any) => {
    onRestoreSession(session)
    toast.success(`Restored session: ${session.name}`)
  }

  const handleToggleDir = async (dirPath: string) => {
    if (expandedDirs.has(dirPath)) {
      setExpandedDirs((prev) => {
        const next = new Set(prev)
        next.delete(dirPath)
        return next
      })
    } else {
      if (!dirChildren[dirPath]) {
        try {
          const res = await filesApi.listFiles(dirPath)
          setDirChildren((prev) => ({ ...prev, [dirPath]: res.files || [] }))
        } catch {
          toast.error('Failed to load directory')
        }
      }
      setExpandedDirs((prev) => new Set(prev).add(dirPath))
    }
  }

  const renderFileTree = (fileList: FileInfo[], level = 0): JSX.Element[] => {
    return fileList.map((file) => (
      <div key={file.path}>
        {file.type === 'directory' ? (
          <div>
            <button
              onClick={() => handleToggleDir(file.path)}
              className="w-full text-left px-2 py-1 text-sm hover:bg-slate-100 rounded flex items-center gap-1"
            >
              <span className="w-4 text-xs">{expandedDirs.has(file.path) ? '▼' : '▶'}</span>
              <span>📁 {file.name}</span>
            </button>
            {expandedDirs.has(file.path) && dirChildren[file.path] && (
              <div style={{ paddingLeft: `${level * 12 + 12}px` }}>
                {renderFileTree(dirChildren[file.path], level + 1)}
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-1 px-2 py-1 text-sm hover:bg-slate-100 rounded group">
            <input
              type="checkbox"
              checked={selectedFiles.has(file.path)}
              onChange={(e) => onSelectFile(file.path, e.target.checked)}
              className="w-4 h-4"
            />
            <span className="flex-1 truncate">📄 {file.name}</span>
            <div className="hidden group-hover:flex gap-1">
              <button
                onClick={() => onFileView(file)}
                className="px-2 py-0.5 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded"
              >
                View
              </button>
              <button
                onClick={() => onAddToContext(file)}
                className="px-2 py-0.5 bg-green-500 hover:bg-green-600 text-white text-xs rounded"
              >
                +
              </button>
            </div>
          </div>
        )}
      </div>
    ))
  }

  const handleAddSkillClick = () => {
    if (!newSkillName.trim() || !newSkillContent.trim()) {
      toast.error('Please enter skill name and content')
      return
    }
    onAddSkill(newSkillName, newSkillContent)
    setNewSkillName('')
    setNewSkillContent('')
  }

  const handleDeleteSkillClick = (id: string) => {
    onDeleteSkill(id)
  }

  return (
    <div className="w-72 flex-shrink-0 border-r bg-white flex flex-col">
      {/* Header */}
      <div className="p-3 border-b flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold text-slate-900">Workspace</h2>
          <div className="flex gap-1">
            <button
              onClick={() => setShowSkillManager(!showSkillManager)}
              className="px-2 py-1 bg-purple-200 hover:bg-purple-300 rounded text-xs font-medium"
              title="Manage skills"
            >
              ✨ ({allSkills.length})
            </button>
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="px-2 py-1 bg-slate-200 hover:bg-slate-300 rounded text-xs font-medium"
              title="View saved sessions"
            >
              💾 ({savedSessions.length})
            </button>
          </div>
        </div>

        {showSkillManager && (
          <div className="mb-3 p-2 bg-purple-50 border rounded max-h-64 overflow-y-auto">
            <p className="text-xs font-semibold text-purple-700 mb-2">Skill Manager</p>

            {allSkills.length > 0 && (
              <div className="space-y-1 mb-3 pb-3 border-b">
                {allSkills.map((skill) => {
                  const isSelected = selectedSkills.some((s) => s.id === skill.id)
                  return (
                    <div key={skill.id} className="flex items-center gap-2 p-1 bg-white rounded text-xs">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => onSelectSkill({ id: skill.id, name: skill.name }, e.target.checked)}
                        className="w-3 h-3"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">{skill.name}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteSkillClick(skill.id)}
                        className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs flex-shrink-0"
                      >
                        Delete
                      </button>
                    </div>
                  )
                })}
              </div>
            )}

            <div className="space-y-2">
              <p className="text-xs font-semibold text-purple-700">Add New Skill</p>
              <input
                type="text"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                placeholder="Skill name..."
                className="w-full px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <textarea
                value={newSkillContent}
                onChange={(e) => setNewSkillContent(e.target.value)}
                placeholder="Paste skill content..."
                className="w-full px-2 py-1 text-xs border border-slate-300 rounded font-mono max-h-24 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={3}
              />
              <button
                onClick={handleAddSkillClick}
                className="w-full px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-medium"
              >
                Add Skill
              </button>
            </div>
          </div>
        )}

        {showSessions && (
          <div className="mb-3 p-2 bg-slate-50 border rounded max-h-48 overflow-y-auto">
            <p className="text-xs font-semibold text-slate-700 mb-2">Saved Sessions</p>
            {savedSessions.length === 0 ? (
              <p className="text-xs text-slate-500">No saved sessions</p>
            ) : (
              <div className="space-y-1 mb-3">
                {savedSessions.map((session) => (
                  <div key={session.id} className="flex items-start gap-1 p-1 bg-white rounded border text-xs">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">{session.name}</p>
                      <p className="text-slate-600 truncate">{session.projectRoot}</p>
                      <p className="text-slate-500">{session.messageCount} messages</p>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button
                        onClick={() => handleRestoreSession(session)}
                        className="px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs"
                      >
                        Restore
                      </button>
                      <button
                        onClick={() => handleDeleteSession(session.id)}
                        className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {projectRoot && (
              <div className="mt-3 pt-2 border-t">
                <p className="text-xs font-semibold text-slate-700 mb-2">Save Current Session</p>
                <div className="flex gap-1">
                  <input
                    type="text"
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleSaveCurrentSession()
                      }
                    }}
                    placeholder="Session name..."
                    className="flex-1 px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={handleSaveCurrentSession}
                    className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs whitespace-nowrap"
                  >
                    Save
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {showInput ? (
          <div className="flex flex-col gap-2">
            <input
              type="text"
              value={projectPathInput}
              onChange={(e) => onProjectPathChange(e.target.value)}
              placeholder="/path/to/project"
              className="px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onOpenProject(projectPathInput)
                  setShowInput(false)
                }
              }}
            />
            <div className="flex gap-2">
              <button
                onClick={() => {
                  onOpenProject(projectPathInput)
                  setShowInput(false)
                }}
                className="flex-1 px-2 py-1 bg-primary-600 hover:bg-primary-700 text-white rounded text-xs font-medium"
              >
                OK
              </button>
              <button
                onClick={() => setShowInput(false)}
                className="flex-1 px-2 py-1 bg-slate-200 hover:bg-slate-300 rounded text-xs font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : projectRoot ? (
          <>
            <div className="flex items-center gap-2 mb-2">
              <p className="text-xs text-slate-600 truncate flex-1">{projectRoot}</p>
              <button
                onClick={() => {
                  setShowInput(true)
                }}
                className="px-2 py-1 bg-slate-300 hover:bg-slate-400 rounded text-xs font-medium flex-shrink-0"
                title="Change project path"
              >
                ✏️
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={onInitAgentMd}
                className="flex-1 px-2 py-1 bg-slate-200 hover:bg-slate-300 rounded text-xs font-medium"
              >
                Init agent.md
              </button>
              <button
                onClick={onSaveAgentMd}
                disabled={agentMdSaving}
                className="flex-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium disabled:bg-slate-400"
              >
                {agentMdSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </>
        ) : (
          <button
            onClick={() => setShowInput(true)}
            className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded text-sm font-medium"
          >
            ✏️ Open Project
          </button>
        )}
      </div>

      {/* Context Files */}
      {contextFiles.length > 0 && (
        <div className="p-2 border-b bg-blue-50 flex-shrink-0">
          <p className="text-xs font-semibold text-blue-900 mb-1">Context ({contextFiles.length})</p>
          {contextFiles.map((f) => (
            <div key={f.path} className="flex items-center justify-between gap-2 py-1 text-xs">
              <span className="truncate text-blue-900">{f.path}</span>
              <button
                onClick={() => onRemoveContext(f.path)}
                className="text-blue-600 hover:text-blue-900 font-bold"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* File Tree */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {projectRoot && (
          <div className="p-2 border-t flex-shrink-0 space-y-1">
            <button
              onClick={onRefreshFileTree}
              className="w-full px-3 py-1 bg-slate-200 hover:bg-slate-300 rounded text-xs font-medium"
            >
              🔄 Refresh
            </button>
            {selectedFiles.size > 0 && (
              <button
                onClick={onAddSelectedFilesToContext}
                className="w-full px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium"
              >
                ➕ Add {selectedFiles.size} to Context
              </button>
            )}
          </div>
        )}
        <div className="flex-1 overflow-y-auto p-2">
          {projectRoot && files.length > 0 ? (
            <div className="space-y-0">{renderFileTree(files)}</div>
          ) : projectRoot ? (
            <p className="text-sm text-slate-500">No files found</p>
          ) : (
            <p className="text-sm text-slate-500">Open a project to view files</p>
          )}
        </div>
      </div>
    </div>
  )
}
