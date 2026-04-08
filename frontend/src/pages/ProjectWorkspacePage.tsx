import { useState, useEffect } from 'react'
import { filesApi } from '@/api/endpoints'
import { WorkspaceLeftPanel } from '@/components/WorkspaceLeftPanel'
import { WorkspaceCenterPanel } from '@/components/WorkspaceCenterPanel'
import { WorkspaceRightPanel } from '@/components/WorkspaceRightPanel'
import { useCodeAction } from '@/hooks/useCodeAction'
import type { FileInfo } from '@/types/files'
import type { Model, ChatMessage } from '@/types/actions'
import toast from 'react-hot-toast'

export const ProjectWorkspacePage = () => {
  // Load saved state on mount
  const savedState = (() => {
    try {
      const saved = localStorage.getItem('jmAgent:workspace:state')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })()

  // State
  const [projectRoot, setProjectRoot] = useState(savedState?.projectRoot || '')
  const [projectPathInput, setProjectPathInput] = useState('')
  const [files, setFiles] = useState<FileInfo[]>([])
  const [contextFiles, setContextFiles] = useState<{ path: string; content: string }[]>([])
  const [viewingFile, setViewingFile] = useState<{ path: string; content: string } | null>(null)
  const [isEditingMode, setIsEditingMode] = useState(false)
  const [editingFile, setEditingFile] = useState<{ path: string; content: string } | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [model, setModel] = useState<Model>('haiku')
  const [centerTab, setCenterTab] = useState<'chat' | 'workflow'>('chat')
  const [rightTab, setRightTab] = useState<'output' | 'agentmd' | 'file'>('output')
  const [outputCode, setOutputCode] = useState('')
  const [outputSavePath, setOutputSavePath] = useState('')
  const [agentMdContent, setAgentMdContent] = useState('')
  const [agentMdSaving, setAgentMdSaving] = useState(false)
  const [selectedSkills, setSelectedSkills] = useState<Array<{ id: string; name: string }>>([])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [allSkills, setAllSkills] = useState<Array<{ id: string; name: string; content: string; enabled: boolean; createdAt: number }>>([])
  const [workflowSteps, setWorkflowSteps] = useState<Array<{ id: string; instruction: string; status: 'pending' | 'running' | 'done' | 'error'; result?: string }>>([])
  const [newStepInput, setNewStepInput] = useState('')
  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false)
  const [streamProgress, setStreamProgress] = useState<string[]>([])
  const [streamStats, setStreamStats] = useState<{ executionTime: number; tokensUsed: { input: number; output: number; total: number } } | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isComposing, setIsComposing] = useState(false)  // Track IME composition

  const { execute, loading: chatLoading } = useCodeAction()

  // Load saved state on mount
  useEffect(() => {
    if (!savedState || !savedState.projectRoot) return

    const loadSavedState = async () => {
      try {
        // 1. Set project root
        setProjectRoot(savedState.projectRoot)
        setModel(savedState.model || 'haiku')

        // 2. Load file tree for the project
        try {
          await filesApi.setProjectRoot(savedState.projectRoot)
          const filesRes = await filesApi.listFiles('')
          setFiles(filesRes.files || [])
          console.log('File tree loaded:', filesRes.files?.length, 'items')
        } catch {
          console.error('Failed to load file tree')
        }

        // 3. Load context files
        if (savedState.contextFiles && savedState.contextFiles.length > 0) {
          try {
            const contextPromises = savedState.contextFiles.map((f: any) =>
              filesApi.readFile(f.path).then((res) => ({
                path: f.path,
                content: res.content,
              }))
            )
            const loaded = await Promise.all(contextPromises)
            setContextFiles(loaded)
            console.log('Context files loaded:', loaded.length, 'files')
          } catch {
            console.error('Failed to load context files')
          }
        }

        // 4. Load agent.md if exists
        try {
          const agentRes = await filesApi.readFile('agent.md')
          setAgentMdContent(agentRes.content)
          console.log('agent.md loaded')
        } catch {
          // no agent.md yet
        }
      } catch (e) {
        console.error('Failed to load saved state:', e)
      }
    }

    loadSavedState()
  }, [])

  // Load skills from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('jmAgent:workspace:skills')
      console.log('Loading skills from localStorage:', saved)
      if (saved) {
        const parsed = JSON.parse(saved)
        console.log('Parsed skills:', parsed)
        setAllSkills(parsed)
      }
    } catch (e) {
      console.error('Failed to load skills:', e)
    }
  }, [])

  // Auto-save workspace state
  useEffect(() => {
    if (!projectRoot) return
    try {
      localStorage.setItem(
        'jmAgent:workspace:state',
        JSON.stringify({
          projectRoot,
          contextFiles: contextFiles.map((f) => ({ path: f.path })),
          messages,
          model,
          timestamp: Date.now(),
        })
      )
    } catch {
      // ignore
    }
  }, [projectRoot, contextFiles, messages, model])

  const handleOpenProject = async (path: string) => {
    const trimmedPath = path.trim()
    if (!trimmedPath) {
      toast.error('Please enter a project path')
      return
    }
    try {
      await filesApi.setProjectRoot(trimmedPath)
      setProjectRoot(trimmedPath)
      setProjectPathInput('')
      const filesRes = await filesApi.listFiles('')
      setFiles(filesRes.files || [])
      try {
        const agentRes = await filesApi.readFile('agent.md')
        setAgentMdContent(agentRes.content)
      } catch {
        // no agent.md yet
      }
      toast.success('✅ Project opened')
    } catch {
      toast.error('Failed to open project')
    }
  }

  const handleRemoveContext = (path: string) => {
    setContextFiles(contextFiles.filter((f) => f.path !== path))
  }

  const handleRefreshFileTree = async () => {
    if (!projectRoot) return
    try {
      const res = await filesApi.listFiles('')
      setFiles(res.files || [])
      toast.success('Files refreshed')
    } catch {
      toast.error('Failed to refresh')
    }
  }

  const handleSaveAgentMd = async () => {
    if (!projectRoot) {
      toast.error('Please open a project')
      return
    }
    try {
      setAgentMdSaving(true)
      await filesApi.writeFile('agent.md', agentMdContent, false)
      toast.success('✅ Saved')
    } catch {
      toast.error('Failed to save')
    } finally {
      setAgentMdSaving(false)
    }
  }

  const handleSendMessage = async () => {
    const input = chatInput.trim()
    if (!input) return

    // Debug log
    console.log('handleSendMessage called with input:', `"${input}"`)

    const userMsg: ChatMessage = { role: 'user', content: input }

    // Update all states atomically
    setMessages((prev) => {
      console.log('Adding message. Current messages:', prev.length)
      return [...prev, userMsg]
    })
    setChatInput('')  // Clear input immediately
    setIsStreaming(true)
    setStreamProgress(['🚀 작업 시작...'])
    setStreamStats(null)

    try {
      // Build context with conversation history (with token management)
      let fullMsg = ''
      const MAX_HISTORY_MESSAGES = 10  // Keep only last 10 messages
      const ESTIMATED_TOKENS_PER_CHAR = 0.25  // Rough estimate

      // 1. Add conversation history (sliding window)
      // Use the PREVIOUS messages (before adding current one)
      if (messages.length > 0) {
        // Get last N messages to manage token growth
        const historyMessages = messages.slice(Math.max(0, messages.length - MAX_HISTORY_MESSAGES))
        const conversationHistory = historyMessages
          .map((msg) => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`)
          .join('\n\n')
        fullMsg += conversationHistory + '\n\n---\n\n'

        const estimatedTokens = Math.round(conversationHistory.length * ESTIMATED_TOKENS_PER_CHAR)
        console.log(`History: ${historyMessages.length} messages (${estimatedTokens} estimated tokens)`)
      }

      // 2. Add context files
      if (contextFiles.length > 0) {
        const filesPrefix = contextFiles.map((f) => `[${f.path}]\n${f.content}`).join('\n\n---\n\n')
        fullMsg += filesPrefix + '\n\n---\n\n'

        const estimatedTokens = Math.round(filesPrefix.length * ESTIMATED_TOKENS_PER_CHAR)
        console.log(`Context files: ${contextFiles.length} files (${estimatedTokens} estimated tokens)`)
      }

      // 3. Add current user message (NOT trimmed again)
      fullMsg += `User: ${input}`
      console.log('Final message to send. Length:', input.length, 'Last char:', input.charCodeAt(input.length - 1))

      // Estimate total tokens
      const totalEstimatedTokens = Math.round(fullMsg.length * ESTIMATED_TOKENS_PER_CHAR)
      console.log('Message sent:', {
        historyMessages: Math.min(messages.length, MAX_HISTORY_MESSAGES),
        contextFiles: contextFiles.length,
        estimatedTotalTokens: totalEstimatedTokens,
        messageLength: input.length
      })

      if (totalEstimatedTokens > 3500) {
        console.warn('⚠️ Token limit approaching! Consider clearing old messages.')
        toast('⚠️ Token usage high - consider starting a new chat', { icon: '⚠️' })
      }

      // Update progress before calling execute
      await new Promise(resolve => setTimeout(resolve, 100))
      setStreamProgress((prev) => [...prev, '📤 Claude 모델에 요청 중...'])

      // Use regular chat endpoint (already authenticated)
      const res = await execute({
        action: 'chat',
        params: { message: fullMsg, model },
      })

      // Update progress after response received
      setStreamProgress((prev) => [...prev, '📥 응답 수신 중...'])
      await new Promise(resolve => setTimeout(resolve, 100))

      if (res?.response) {
        setStreamProgress((prev) => [...prev, '✅ 처리 완료'])

        const assistantMsg: ChatMessage = { role: 'assistant', content: res.response }
        setMessages((prev) => [...prev, assistantMsg])

        // Extract code blocks
        const codeMatch = res.response.match(/```[\w]*\n([\s\S]*?)```/g)
        if (codeMatch) {
          const code = codeMatch
            .map((block: string) => block.replace(/```[\w]*\n/, '').replace(/```$/, ''))
            .join('\n\n')
          setOutputCode(code)
        }

        // Set completion stats
        await new Promise(resolve => setTimeout(resolve, 500))
        setStreamStats({
          executionTime: 0,
          tokensUsed: { input: 0, output: 0, total: 0 },
        })
      }
    } catch (error) {
      console.error('Chat error:', error)
      setStreamProgress((prev) => [...prev, '❌ 오류 발생'])
      toast.error('메시지 전송 실패')
    } finally {
      setIsStreaming(false)
    }
  }

  const handleSaveOutput = async () => {
    if (!outputCode) {
      toast.error('No output to save')
      return
    }
    if (!projectRoot) {
      navigator.clipboard.writeText(outputCode)
      toast.success('Copied to clipboard')
      return
    }

    // Convert absolute path to relative path if needed
    let savePath = outputSavePath || `output/generated_${Date.now()}.txt`
    if (savePath.startsWith('/')) {
      // Absolute path - convert to relative
      if (savePath.startsWith(projectRoot + '/')) {
        savePath = savePath.substring(projectRoot.length + 1)
      } else {
        toast.error('File path must be within project folder')
        return
      }
    }

    try {
      await filesApi.writeFile(savePath, outputCode, true)
      toast.success(`✅ Saved`)
      setOutputSavePath('')
      const res = await filesApi.listFiles('')
      setFiles(res.files || [])
    } catch {
      toast.error('Failed to save')
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(outputCode)
    toast.success('Copied')
  }

  const handleNewChat = () => {
    setMessages([])
    setChatInput('')
    setOutputCode('')
  }

  const handleFileView = async (file: FileInfo) => {
    try {
      const response = await filesApi.readFile(file.path)
      setViewingFile({ path: file.path, content: response.content })
      setRightTab('file')
      setIsEditingMode(false)
    } catch {
      toast.error(`Failed to read file`)
    }
  }

  const handleAddToContext = async (file: FileInfo) => {
    try {
      const response = await filesApi.readFile(file.path)
      const existing = contextFiles.find((f) => f.path === file.path)
      if (!existing) {
        setContextFiles([...contextFiles, { path: file.path, content: response.content }])
        toast.success(`Added to context`)
      }
    } catch {
      toast.error(`Failed to add file`)
    }
  }

  const handleInitAgentMd = () => {
    const template = `---
name: my-agent
description: >
  AI coding agent configuration
---

# Agent Guidelines

## Project Overview
Define your project here

## Tech Stack
Languages and frameworks

## Code Standards
Code style and patterns

## Instructions
Code generation rules
`
    setAgentMdContent(template)
    setRightTab('agentmd')
  }

  const handleRestoreSession = async (session: any) => {
    try {
      // 1. Load project
      setProjectRoot(session.projectRoot)
      const filesRes = await filesApi.listFiles('')
      setFiles(filesRes.files || [])

      // 2. Restore conversation history
      if (session.messages && session.messages.length > 0) {
        setMessages(session.messages)
        console.log('Restored conversation with', session.messages.length, 'messages')
      }

      // 3. Load context files
      if (session.contextFiles && session.contextFiles.length > 0) {
        try {
          const contextPromises = session.contextFiles.map((f: any) =>
            filesApi.readFile(f.path).then((res) => ({
              path: f.path,
              content: res.content,
            }))
          )
          const loadedContext = await Promise.all(contextPromises)
          setContextFiles(loadedContext)
        } catch {
          console.warn('Failed to load some context files')
        }
      }

      toast.success(`✅ Restored session: ${session.name}`)
    } catch (e) {
      console.error('Failed to restore session:', e)
      toast.error('Failed to restore session')
    }
  }

  const handleSelectSkill = (skill: { id: string; name: string }, selected: boolean) => {
    if (selected) {
      setSelectedSkills([...selectedSkills, skill])
    } else {
      setSelectedSkills(selectedSkills.filter((s) => s.id !== skill.id))
    }
  }

  const handleSelectFile = (filePath: string, selected: boolean) => {
    const next = new Set(selectedFiles)
    if (selected) {
      next.add(filePath)
    } else {
      next.delete(filePath)
    }
    setSelectedFiles(next)
  }

  const handleAddSkill = (skillName: string, skillContent: string) => {
    const skill = {
      id: Date.now().toString(),
      name: skillName,
      content: skillContent,
      enabled: true,
      createdAt: Date.now(),
    }
    const updated = [...allSkills, skill]

    // Save to localStorage first
    try {
      localStorage.setItem('jmAgent:workspace:skills', JSON.stringify(updated))
      console.log('Skill saved to localStorage:', updated)
    } catch (e) {
      console.error('Failed to save skills to localStorage:', e)
      toast.error('Failed to save skill')
      return
    }

    // Then update state
    setAllSkills(updated)
    toast.success(`Skill "${skill.name}" added ✅`)
  }

  const handleDeleteSkill = (skillId: string) => {
    const updated = allSkills.filter((s) => s.id !== skillId)

    // Save to localStorage first
    try {
      localStorage.setItem('jmAgent:workspace:skills', JSON.stringify(updated))
      console.log('Skill deleted and saved to localStorage:', updated)
    } catch (e) {
      console.error('Failed to save skills to localStorage:', e)
      toast.error('Failed to delete skill')
      return
    }

    // Then update state
    setAllSkills(updated)
    setSelectedSkills(selectedSkills.filter((s) => s.id !== skillId))
    toast.success('Skill deleted ✅')
  }

  const handleAddSelectedFilesToContext = async () => {
    try {
      const filesToAdd: Array<{ path: string; content: string }> = []
      for (const filePath of selectedFiles) {
        const response = await filesApi.readFile(filePath)
        filesToAdd.push({ path: filePath, content: response.content })
      }
      setContextFiles([...contextFiles, ...filesToAdd])
      setSelectedFiles(new Set())
      toast.success(`Added ${filesToAdd.length} file(s) to context`)
    } catch {
      toast.error('Failed to add files to context')
    }
  }

  const handleAddWorkflowStep = () => {
    if (!newStepInput.trim()) {
      toast.error('Please enter a step instruction')
      return
    }
    const step = {
      id: Date.now().toString(),
      instruction: newStepInput,
      status: 'pending' as const,
    }
    setWorkflowSteps([...workflowSteps, step])
    setNewStepInput('')
    toast.success('Step added')
  }

  const handleRemoveWorkflowStep = (stepId: string) => {
    setWorkflowSteps(workflowSteps.filter((s) => s.id !== stepId))
  }

  const handleRunWorkflow = async () => {
    if (workflowSteps.length === 0) {
      toast.error('No workflow steps to run')
      return
    }

    setIsWorkflowRunning(true)
    setStreamProgress([])
    setStreamStats(null)
    setIsStreaming(true)

    try {
      for (const step of workflowSteps) {
        // Update step status
        setWorkflowSteps((prev) =>
          prev.map((s) =>
            s.id === step.id ? { ...s, status: 'running' as const } : s
          )
        )

        // Add progress message
        setStreamProgress((prev) => [...prev, `▶️  Running: ${step.instruction}`])

        try {
          // Execute step as chat message
          let stepMessage = step.instruction
          if (contextFiles.length > 0) {
            const prefix = contextFiles.map((f) => `[${f.path}]\n${f.content}`).join('\n\n---\n\n')
            stepMessage = `${prefix}\n\n${step.instruction}`
          }

          const res = await execute({
            action: 'chat',
            params: { message: stepMessage, model },
          })

          setStreamProgress((prev) => [...prev, `✅ Complete: ${step.instruction}`])

          // Update step status
          setWorkflowSteps((prev) =>
            prev.map((s) =>
              s.id === step.id
                ? { ...s, status: 'done' as const, result: res?.response }
                : s
            )
          )

          // Extract code if available
          if (res?.response) {
            const codeMatch = res.response.match(/```[\w]*\n([\s\S]*?)```/g)
            if (codeMatch) {
              const code = codeMatch
                .map((block: string) => block.replace(/```[\w]*\n/, '').replace(/```$/, ''))
                .join('\n\n')
              setOutputCode(code)
            }
          }
        } catch (error) {
          setStreamProgress((prev) => [...prev, `❌ Failed: ${step.instruction}`])
          setWorkflowSteps((prev) =>
            prev.map((s) =>
              s.id === step.id ? { ...s, status: 'error' as const } : s
            )
          )
        }
      }

      // Set completion stats
      setStreamStats({
        executionTime: workflowSteps.length,
        tokensUsed: { input: 0, output: 0, total: 0 },
      })
    } finally {
      setIsStreaming(false)
      setIsWorkflowRunning(false)
    }
  }

  return (
    <div className="flex flex-row w-full h-full bg-slate-50">
      <WorkspaceLeftPanel
        projectRoot={projectRoot}
        files={files}
        contextFiles={contextFiles}
        projectPathInput={projectPathInput}
        agentMdSaving={agentMdSaving}
        messages={messages}
        selectedSkills={selectedSkills}
        selectedFiles={selectedFiles}
        allSkills={allSkills}
        onOpenProject={handleOpenProject}
        onProjectPathChange={setProjectPathInput}
        onRefreshFileTree={handleRefreshFileTree}
        onRemoveContext={handleRemoveContext}
        onFileView={handleFileView}
        onAddToContext={handleAddToContext}
        onInitAgentMd={handleInitAgentMd}
        onSaveAgentMd={handleSaveAgentMd}
        onRestoreSession={handleRestoreSession}
        onSelectSkill={handleSelectSkill}
        onSelectFile={handleSelectFile}
        onAddSelectedFilesToContext={handleAddSelectedFilesToContext}
        onAddSkill={handleAddSkill}
        onDeleteSkill={handleDeleteSkill}
      />

      <WorkspaceCenterPanel
        centerTab={centerTab}
        setCenterTab={setCenterTab}
        messages={messages}
        chatInput={chatInput}
        chatLoading={chatLoading}
        model={model}
        contextFiles={contextFiles}
        isStreaming={isStreaming}
        streamProgress={streamProgress}
        streamStats={streamStats}
        selectedSkills={selectedSkills}
        selectedFiles={selectedFiles}
        workflowSteps={workflowSteps}
        newStepInput={newStepInput}
        isWorkflowRunning={isWorkflowRunning}
        onModelChange={setModel}
        onNewChat={handleNewChat}
        onChatInputChange={setChatInput}
        onSendMessage={handleSendMessage}
        onKeyDown={(e) => {
          // Only handle Enter if not composing (Korean/Japanese input)
          if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
            e.preventDefault()
            handleSendMessage()
          }
        }}
        onCompositionStart={() => {
          setIsComposing(true)
          console.log('IME composition started')
        }}
        onCompositionEnd={() => {
          setIsComposing(false)
          console.log('IME composition ended')
        }}
        onAddWorkflowStep={handleAddWorkflowStep}
        onRemoveWorkflowStep={handleRemoveWorkflowStep}
        onRunWorkflow={handleRunWorkflow}
        onNewStepInputChange={setNewStepInput}
      />

      <WorkspaceRightPanel
        rightTab={rightTab}
        setRightTab={setRightTab}
        outputCode={outputCode}
        outputSavePath={outputSavePath}
        agentMdContent={agentMdContent}
        viewingFile={viewingFile}
        isEditingMode={isEditingMode}
        agentMdSaving={agentMdSaving}
        projectRoot={projectRoot}
        onCopyToClipboard={copyToClipboard}
        onSaveOutput={handleSaveOutput}
        onOutputPathChange={setOutputSavePath}
        onSaveAgentMd={handleSaveAgentMd}
        onAgentMdChange={setAgentMdContent}
        onStartEditFile={() => {
          if (viewingFile) {
            setEditingFile({ ...viewingFile })
            setIsEditingMode(true)
          }
        }}
        onSaveEditedFile={async () => {
          if (!editingFile) return
          try {
            await filesApi.writeFile(editingFile.path, editingFile.content, false)
            setViewingFile(editingFile)
            setIsEditingMode(false)
            toast.success('✅ Saved')
            const res = await filesApi.listFiles('')
            setFiles(res.files || [])
          } catch {
            toast.error('Failed to save')
          }
        }}
        onCancelEditFile={() => {
          setIsEditingMode(false)
          setEditingFile(null)
        }}
      />
    </div>
  )
}
