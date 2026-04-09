import { useState, useEffect } from 'react'
import { filesApi } from '@/api/endpoints'
import { WorkspaceLeftPanel } from '@/components/WorkspaceLeftPanel'
import { WorkspaceCenterPanel } from '@/components/WorkspaceCenterPanel'
import { WorkspaceRightPanel } from '@/components/WorkspaceRightPanel'
import { useChatStream } from '@/hooks/useChatStream'
import type { FileInfo } from '@/types/files'
import type { Model, ChatMessage } from '@/types/actions'
import toast from 'react-hot-toast'

// Generate UUID for conversation ID
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

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
  const [conversationId, setConversationId] = useState<string>(() => generateUUID())
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
  const [workflowSteps, setWorkflowSteps] = useState<Array<{
    id: string
    instruction: string
    status: 'pending' | 'running' | 'done' | 'error'
    result?: string
    contextFiles?: Array<{ path: string; content: string }>  // 단계별 컨텍스트 스냅샷
    skills?: Array<{ id: string; name: string }>             // 단계별 스킬 스냅샷
  }>>([])
  const [newStepInput, setNewStepInput] = useState('')
  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false)
  const [streamProgress, setStreamProgress] = useState<string[]>([])
  const [streamStats, setStreamStats] = useState<{ executionTime: number; tokensUsed: { input: number; output: number; total: number } } | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isComposing, setIsComposing] = useState(false)  // Track IME composition
  const [leftPanelWidth, setLeftPanelWidth] = useState<number>(() => {
    // localStorage에서 저장된 너비 복원 (기본값: 280px)
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('jmAgent:leftPanelWidth')
      return saved ? parseInt(saved, 10) : 280
    }
    return 280
  })
  const [isResizing, setIsResizing] = useState(false)

  const { sendChatStream } = useChatStream()

  // 리사이징 핸들러
  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = e.clientX
      // 최소 200px ~ 최대 600px 범위 제한
      if (newWidth >= 200 && newWidth <= 600) {
        setLeftPanelWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.addEventListener('selectstart', (e) => e.preventDefault())

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  // 너비 변경 시 localStorage에 저장
  useEffect(() => {
    localStorage.setItem('jmAgent:leftPanelWidth', leftPanelWidth.toString())
  }, [leftPanelWidth])

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

  // Parse file creation directives from Claude's response
  // Format: [FILE_CREATE:{"path":"filename","content":"..."}]
  const parseFileCreations = (content: string): { files: Array<{path: string; content: string}>; cleanContent: string } => {
    const fileRegex = /\[FILE_CREATE:({[\s\S]*?})\]/g
    const files: Array<{path: string; content: string}> = []
    let cleanContent = content

    let match
    while ((match = fileRegex.exec(content)) !== null) {
      try {
        const fileObj = JSON.parse(match[1])
        if (fileObj.path && fileObj.content) {
          files.push(fileObj)
          cleanContent = cleanContent.replace(match[0], '')
        }
      } catch {
        // Skip malformed JSON
      }
    }

    return { files, cleanContent: cleanContent.trim() }
  }

  // Create files in the project
  const createFilesFromResponse = async (files: Array<{path: string; content: string}>): Promise<Array<{path: string; status: 'success' | 'error'; bytes?: number; error?: string}>> => {
    if (files.length === 0) return []

    const results: Array<{path: string; status: 'success' | 'error'; bytes?: number; error?: string}> = []

    for (const file of files) {
      try {
        await filesApi.writeFile(file.path, file.content, true)
        results.push({
          path: file.path,
          status: 'success',
          bytes: file.content.length,
        })
      } catch (error) {
        results.push({
          path: file.path,
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error',
        })
      }
    }

    return results
  }

  // Transform file creation results into status message
  const buildFileStatusMessage = (results: Array<{path: string; status: 'success' | 'error'; bytes?: number; error?: string}>): string => {
    const lines = results.map((r) => {
      if (r.status === 'success') {
        return `✅ ${r.path} 생성 완료 (${r.bytes} bytes)`
      } else {
        return `❌ ${r.path} 생성 실패: ${r.error}`
      }
    })
    return lines.join('\n')
  }

  const handleSendMessage = async () => {
    const input = chatInput.trim()
    if (!input) return

    const userMsg: ChatMessage = { role: 'user', content: input }

    // Add user message to history immediately
    setMessages((prev) => [...prev, userMsg])
    setChatInput('')
    setIsStreaming(true)
    setStreamProgress([])  // Show simple loading spinner, no progress details
    setStreamStats(null)

    try {
      // Token estimation with Korean character support
      // Korean chars are much heavier than English: 1 Korean char = 1-2 tokens
      // English chars are lighter: 1 English char = 0.25 tokens
      const estimateTokens = (text: string): number => {
        let tokens = 0
        for (const char of text) {
          const code = char.charCodeAt(0)
          // Korean: AC00-D7A3 (가-힣)
          if (code >= 0xac00 && code <= 0xd7a3) {
            tokens += 1.5  // Korean: 1.5 tokens per char
          } else if (code < 128) {
            tokens += 0.25  // ASCII: 0.25 tokens per char
          } else {
            tokens += 0.5   // Other Unicode: 0.5 tokens per char
          }
        }
        return Math.round(tokens)
      }

      // Increased budget since backend manages history via conversation_id
      // Frontend only handles file context
      const MAX_FILE_TOKENS = 3000       // Max tokens per file (was 800)
      const MAX_TOTAL_CONTEXT = 10000    // Max total context tokens (was 2000)

      // 1. Build context files with token budget (CRITICAL for token savings)
      let contextPrefix = ''
      let totalContextTokens = 0

      if (contextFiles.length > 0) {
        const contextLines: string[] = []

        for (const file of contextFiles) {
          const fileTokens = estimateTokens(file.content)

          // Skip if total would exceed budget
          if (totalContextTokens + fileTokens > MAX_TOTAL_CONTEXT) {
            toast(`⚠️ ${file.path} 제외됨 (토큰 한도 초과)`, { icon: '⚠️' })
            continue
          }

          // Trim file if too large
          const content =
            fileTokens > MAX_FILE_TOKENS
              ? file.content.slice(0, MAX_FILE_TOKENS * 4) + '\n... (truncated)'
              : file.content

          contextLines.push(`[${file.path}]\n${content}`)
          totalContextTokens += Math.min(fileTokens, MAX_FILE_TOKENS)
        }

        if (contextLines.length > 0) {
          contextPrefix = contextLines.join('\n\n---\n\n') + '\n\n---\n\n'
          console.log(
            `Context files: ${contextLines.length}/${contextFiles.length} files (${totalContextTokens} tokens)`
          )
        }
      }

      // 2. Build skill instructions (prepend to message)
      let skillPrefix = ''
      if (selectedSkills.length > 0) {
        const selectedSkillContents = selectedSkills
          .map((selected) => {
            const skillDef = allSkills.find((s) => s.id === selected.id)
            return skillDef ? skillDef.content : ''
          })
          .filter(Boolean)

        if (selectedSkillContents.length > 0) {
          skillPrefix = selectedSkillContents.join('\n\n---\n\n') + '\n\n'
          console.log(`Using ${selectedSkillContents.length} skill(s)`)
        }
      }

      // 3. Build message (NO history inlining — backend manages via conversation_id)
      const message = skillPrefix + contextPrefix + input

      const totalTokens = estimateTokens(message)
      if (totalTokens > 8000) {
        // Warn only if approaching limits (8k tokens ≈ 32k chars)
        toast('⚠️ Very high token usage - consider starting new chat', { icon: '⚠️' })
      }

      setStreamProgress((prev) => [...prev, '📤 Claude에 전송 중...'])

      // 3. Use SSE streaming (real-time progress, no timeout issues)
      const result = await sendChatStream({
        message,
        conversation_id: conversationId,  // Backend maintains history with this ID
        model,
      })

      if (!result) return  // Cancelled

      const { content, stats } = result

      setStreamProgress((prev) => [...prev, '📥 응답 처리 중...'])

      // Parse file creation directives from response
      const { files: filesToCreate, cleanContent } = parseFileCreations(content)

      let finalContent = cleanContent
      let fileStatusMessage = ''

      // Create files if any are specified
      if (filesToCreate.length > 0) {
        const creationResults = await createFilesFromResponse(filesToCreate)
        fileStatusMessage = buildFileStatusMessage(creationResults)

        // Reload file tree to show newly created files
        try {
          const res = await filesApi.listFiles('')
          setFiles(res.files || [])
        } catch {
          console.error('Failed to reload file tree')
        }

        // Prepend file status to content (or replace if no other content)
        if (finalContent) {
          finalContent = fileStatusMessage + '\n\n' + finalContent
        } else {
          finalContent = fileStatusMessage
        }
      }

      // Add assistant message with final content (file status + any remaining text)
      const assistantMsg: ChatMessage = { role: 'assistant', content: finalContent }
      setMessages((prev) => [...prev, assistantMsg])

      // Extract code blocks (only from non-file-creation content)
      const codeMatch = cleanContent.match(/```[\w]*\n([\s\S]*?)```/g)
      if (codeMatch) {
        const code = codeMatch
          .map((block: string) => block.replace(/```[\w]*\n/, '').replace(/```$/, ''))
          .join('\n\n')
        setOutputCode(code)
      }

      // Show completion stats
      setStreamProgress((prev) => [...prev, '✅ 완료!'])
      if (stats) {
        setStreamStats(stats)
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
    setConversationId(generateUUID())  // New chat = new conversation
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
    // 단계 추가 시점에 현재 선택된 컨텍스트와 스킬을 스냅샷으로 저장
    const step = {
      id: Date.now().toString(),
      instruction: newStepInput,
      status: 'pending' as const,
      contextFiles: [...contextFiles],  // 스냅샷
      skills: [...selectedSkills],      // 스냅샷
    }
    setWorkflowSteps([...workflowSteps, step])
    setNewStepInput('')
    toast.success(`Step added (${contextFiles.length} context files, ${selectedSkills.length} skills)`)
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

    let totalExecutionTime = 0
    let totalInputTokens = 0
    let totalOutputTokens = 0

    try {
      for (const step of workflowSteps) {
        // Update step status to running
        setWorkflowSteps((prev) =>
          prev.map((s) =>
            s.id === step.id ? { ...s, status: 'running' as const } : s
          )
        )

        setStreamProgress((prev) => [...prev, `▶️  Running: ${step.instruction}`])

        try {
          // 단계별 컨텍스트 사용 (없으면 전역 fallback)
          const stepContextFiles = step.contextFiles ?? contextFiles
          const stepSkills = step.skills ?? selectedSkills

          // 스킬 프리픽스 build (handleSendMessage와 동일한 방식)
          let skillPrefix = ''
          if (stepSkills.length > 0) {
            const selectedSkillContents = stepSkills
              .map((selected) => {
                const skillDef = allSkills.find((s) => s.id === selected.id)
                return skillDef ? skillDef.content : ''
              })
              .filter(Boolean)

            if (selectedSkillContents.length > 0) {
              skillPrefix = selectedSkillContents.join('\n\n---\n\n') + '\n\n'
            }
          }

          // 컨텍스트 프리픽스 build
          let contextPrefix = ''
          if (stepContextFiles.length > 0) {
            const contextLines = stepContextFiles.map((f) => `[${f.path}]\n${f.content}`)
            contextPrefix = contextLines.join('\n\n---\n\n') + '\n\n'
          }

          // 최종 메시지
          const stepMessage = skillPrefix + contextPrefix + step.instruction

          // SSE 스트리밍 사용 (blocking execute 대신)
          const result = await sendChatStream({
            message: stepMessage,
            conversation_id: conversationId,
            model,
          })

          if (!result) {
            throw new Error('Stream cancelled')
          }

          const { content, stats } = result

          // 파일 생성 처리
          const { files: filesToCreate, cleanContent } = parseFileCreations(content)
          let fileStatusMessage = ''

          if (filesToCreate.length > 0) {
            const creationResults = await createFilesFromResponse(filesToCreate)
            fileStatusMessage = buildFileStatusMessage(creationResults)

            // 파일 트리 다시 로드
            try {
              const res = await filesApi.listFiles('')
              setFiles(res.files || [])
            } catch {
              console.error('Failed to reload file tree')
            }
          }

          // 응답 저장
          const finalContent = fileStatusMessage
            ? fileStatusMessage + (cleanContent ? '\n\n' + cleanContent : '')
            : cleanContent

          // 코드 블록 추출
          if (cleanContent) {
            const codeMatch = cleanContent.match(/```[\w]*\n([\s\S]*?)```/g)
            if (codeMatch) {
              const code = codeMatch
                .map((block: string) => block.replace(/```[\w]*\n/, '').replace(/```$/, ''))
                .join('\n\n')
              setOutputCode(code)
            }
          }

          // 단계 상태 업데이트
          setWorkflowSteps((prev) =>
            prev.map((s) =>
              s.id === step.id
                ? { ...s, status: 'done' as const, result: finalContent }
                : s
            )
          )

          setStreamProgress((prev) => [...prev, `✅ Complete: ${step.instruction}`])

          // 토큰 누적
          if (stats) {
            totalExecutionTime += stats.executionTime
            totalInputTokens += stats.tokensUsed.input
            totalOutputTokens += stats.tokensUsed.output
          }
        } catch (error) {
          console.error('Workflow step error:', error)
          setStreamProgress((prev) => [...prev, `❌ Failed: ${step.instruction}`])
          setWorkflowSteps((prev) =>
            prev.map((s) =>
              s.id === step.id ? { ...s, status: 'error' as const } : s
            )
          )
        }
      }

      // 최종 stats
      setStreamStats({
        executionTime: totalExecutionTime,
        tokensUsed: {
          input: totalInputTokens,
          output: totalOutputTokens,
          total: totalInputTokens + totalOutputTokens,
        },
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
        width={leftPanelWidth}
        onResizeStart={() => setIsResizing(true)}
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
        chatLoading={isStreaming}  // Use isStreaming for UI feedback
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
