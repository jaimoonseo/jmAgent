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
  const [outputBlocks, setOutputBlocks] = useState<CodeBlock[]>([])
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
    createdFiles?: string[]                                   // 이 단계에서 생성된 파일 경로 목록
    dependsOn?: string[]                                       // 이전 step ID 목록 (실행 시 결과물을 컨텍스트에 주입)
    streamingContent?: string                                  // 실행 중 수신된 스트리밍 텍스트
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

  // Extract code blocks from Claude's response
  // Format 1: ```language\ncode\n```
  // Format 2: Large text sections separated by --- (for skills that output markdown directly)
  interface CodeBlock {
    language: string
    code: string
    suggestedFilename: string
  }

  const inferFilename = (code: string, language: string, index: number): string => {
    // Try to detect explicit filename from content headers
    const lines = code.split('\n')
    for (const line of lines.slice(0, 10)) {
      if (!line.match(/^#+\s/)) continue

      // "## 파일: filename.ext"
      const fileMatch = line.match(/^#+\s+파일:\s*([a-zA-Z0-9._\-]+\.[a-z]+)/)
      if (fileMatch) return fileMatch[1].trim()

      // "# filename.ext" (exact filename in header)
      const headerMatch = line.match(/^#+\s+([a-zA-Z0-9._\-]+\.[a-z]+)$/)
      if (headerMatch) return headerMatch[1].trim()
    }

    // Fallback: language-based generic name
    const ext: Record<string, string> = { html: 'html', markdown: 'md', python: 'py', javascript: 'js', typescript: 'ts', css: 'css', json: 'json', lua: 'lua' }
    return `output_${index}.${ext[language] || 'txt'}`
  }

  const extractCodeBlocks = (content: string): { codeBlocks: CodeBlock[]; cleanContent: string } => {
    const codeBlocks: CodeBlock[] = []
    let cleanContent = ''

    // Try Format 0: ===FILE:filename=== ... ===END_FILE=== delimiter format (most reliable)
    const fileDelimiterRegex = /===FILE:(.+?)===\n([\s\S]*?)===END_FILE===/g
    let delimiterMatch
    while ((delimiterMatch = fileDelimiterRegex.exec(content)) !== null) {
      const filename = delimiterMatch[1].trim()
      const fileContent = delimiterMatch[2].trim()

      // Detect language from filename
      let language = 'plaintext'
      if (filename.endsWith('.md')) language = 'markdown'
      else if (filename.endsWith('.html')) language = 'html'
      else if (filename.endsWith('.py')) language = 'python'
      else if (filename.endsWith('.js') || filename.endsWith('.ts')) language = 'javascript'

      codeBlocks.push({ language, code: fileContent, suggestedFilename: filename })
      console.log(`  ✅ ${filename} (${language}, ${fileContent.length} bytes)`)
    }

    if (codeBlocks.length > 0) {
      // Remove the file blocks from display content
      cleanContent = content.replace(/===FILE:.+?===\n[\s\S]*?===END_FILE===/g, '').trim()
      console.log(`🎉 Extracted ${codeBlocks.length} file(s) via delimiter format`)
      return { codeBlocks, cleanContent }
    }

    // Try Format 0.5: ===FILE:filename=== without ===END_FILE=== (truncated response)
    // When Claude hits token limit, END_FILE marker is missing. Treat rest of content as the file.
    const truncatedFileRegex = /===FILE:(.+?)===\n([\s\S]+)/g
    let truncatedMatch
    const truncatedBlocks: CodeBlock[] = []
    while ((truncatedMatch = truncatedFileRegex.exec(content)) !== null) {
      const filename = truncatedMatch[1].trim()
      // Check if the remaining content contains another ===FILE: (multiple files, last one truncated)
      const fileContent = truncatedMatch[2]
      // Split by next ===FILE: if present
      const nextFileIdx = fileContent.indexOf('===FILE:')
      const actualContent = nextFileIdx >= 0 ? fileContent.substring(0, nextFileIdx).trim() : fileContent.trim()

      let language = 'plaintext'
      if (filename.endsWith('.md')) language = 'markdown'
      else if (filename.endsWith('.html')) language = 'html'
      else if (filename.endsWith('.py')) language = 'python'
      else if (filename.endsWith('.js') || filename.endsWith('.ts')) language = 'javascript'

      truncatedBlocks.push({ language, code: actualContent, suggestedFilename: filename })
      console.log(`  ⚠️ ${filename} (truncated, ${actualContent.length} bytes)`)
    }

    if (truncatedBlocks.length > 0) {
      cleanContent = ''
      console.log(`🔧 Extracted ${truncatedBlocks.length} file(s) via truncated delimiter format`)
      return { codeBlocks: truncatedBlocks, cleanContent }
    }

    // Try Format 1: Explicit code blocks
    const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g
    let match
    let lastIndex = 0
    let blockIndex = 0

    while ((match = codeBlockRegex.exec(content)) !== null) {
      const language = match[1] || 'plaintext'
      const code = match[2].trim()
      const suggestedFilename = inferFilename(code, language, blockIndex)
      codeBlocks.push({ language, code, suggestedFilename })
      cleanContent += content.substring(lastIndex, match.index)
      lastIndex = codeBlockRegex.lastIndex
      blockIndex++
    }
    cleanContent += content.substring(lastIndex)

    console.log(`📦 Extracted ${codeBlocks.length} blocks (${cleanContent.length} chars remaining)`)
    return { codeBlocks, cleanContent: cleanContent.trim() }
  }

  // (Removed FILE_CREATE parsing - now using simple code block extraction)
  // Users can manually save code from the Output tab, or we can enhance this
  // later to intelligently infer filenames from code comments

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
      // Clean skill content: remove FILE_CREATE format and replace with delimiter format
      const cleanSkillContent = (content: string): string => {
        // Remove the entire "📤 출력 형식" section that contains FILE_CREATE
        let cleaned = content.replace(/## 📤 출력 형식[\s\S]*?(?=\n## |$)/, '')
        // Also remove any standalone FILE_CREATE references
        cleaned = cleaned.replace(/\[FILE_CREATE:[\s\S]*?\]/g, '')
        // Remove "File Generator" template instructions
        cleaned = cleaned.replace(/Each file MUST be wrapped in \[FILE_CREATE[\s\S]*?multiple files/g, '')
        return cleaned.trim()
      }

      let skillPrefix = ''
      if (selectedSkills.length > 0) {
        const selectedSkillContents = selectedSkills
          .map((selected) => {
            const skillDef = allSkills.find((s) => s.id === selected.id)
            return skillDef ? cleanSkillContent(skillDef.content) : ''
          })
          .filter(Boolean)

        if (selectedSkillContents.length > 0) {
          skillPrefix = selectedSkillContents.join('\n\n---\n\n') + '\n\n'
          console.log(`Using ${selectedSkillContents.length} skill(s) (FILE_CREATE cleaned)`)
        }
      }

      // 3. Build message (NO history inlining — backend manages via conversation_id)
      // File format instruction placed AFTER skill (Claude follows last instruction best)
      const fileFormatInstruction = `

[OUTPUT FORMAT - MANDATORY]
파일 출력 시 반드시 아래 구분자를 사용하세요. 마크다운 코드블록(\`\`\`)은 사용하지 마세요.

===FILE:파일명.확장자===
파일 전체 내용 (줄바꿈 그대로, 이스케이프 없이)
===END_FILE===

`
      const message = skillPrefix + contextPrefix + input + fileFormatInstruction

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

      // Extract code blocks from response
      const { codeBlocks, cleanContent } = extractCodeBlocks(content)

      // If we have code blocks, show them in output tab
      if (codeBlocks.length > 0) {
        setOutputBlocks(codeBlocks)
        setRightTab('output')
      }

      // Add assistant message
      const assistantMsg: ChatMessage = { role: 'assistant', content: cleanContent || content }
      setMessages((prev) => [...prev, assistantMsg])

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

  // Save a single output block
  const handleSaveBlock = async (block: CodeBlock, _index: number) => {
    console.log(`💾 Saving block: ${block.suggestedFilename}, projectRoot=${projectRoot}, codeLength=${block.code.length}`)

    if (!projectRoot) {
      navigator.clipboard.writeText(block.code)
      toast.success(`✅ Copied to clipboard: ${block.suggestedFilename}`)
      return
    }

    try {
      const savePath = block.suggestedFilename
      console.log(`  Writing file: ${savePath}`)
      await filesApi.writeFile(savePath, block.code, true)
      console.log(`  ✅ File written successfully`)
      toast.success(`✅ Saved: ${savePath}`)
      const res = await filesApi.listFiles('')
      setFiles(res.files || [])
    } catch (error) {
      console.error(`❌ Save error:`, error)
      toast.error(`Failed to save ${block.suggestedFilename}: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Save all output blocks at once
  const handleSaveAllOutput = async () => {
    console.log(`💾 SaveAll: ${outputBlocks.length} blocks, projectRoot=${projectRoot}`)

    if (outputBlocks.length === 0) {
      toast.error('No output to save')
      return
    }

    if (!projectRoot) {
      // Copy all to clipboard
      const allCode = outputBlocks.map((b) => b.code).join('\n\n---\n\n')
      navigator.clipboard.writeText(allCode)
      toast.success(`✅ Copied ${outputBlocks.length} block(s) to clipboard`)
      return
    }

    try {
      let saved = 0
      for (const block of outputBlocks) {
        try {
          console.log(`  Saving: ${block.suggestedFilename}`)
          await filesApi.writeFile(block.suggestedFilename, block.code, true)
          console.log(`  ✅ Saved: ${block.suggestedFilename}`)
          saved++
        } catch (e) {
          console.error(`  ❌ Failed to save ${block.suggestedFilename}`, e)
        }
      }

      toast.success(`✅ Saved ${saved}/${outputBlocks.length} file(s)`)
      const res = await filesApi.listFiles('')
      setFiles(res.files || [])
    } catch (error) {
      console.error('SaveAll error:', error)
      toast.error('Failed to save files')
    }
  }

  const copyToClipboard = (block?: CodeBlock) => {
    if (block) {
      navigator.clipboard.writeText(block.code)
      toast.success(`Copied: ${block.suggestedFilename}`)
    } else if (outputBlocks.length > 0) {
      const allCode = outputBlocks.map((b) => b.code).join('\n\n---\n\n')
      navigator.clipboard.writeText(allCode)
      toast.success(`Copied ${outputBlocks.length} block(s)`)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setChatInput('')
    setOutputBlocks([])
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

      // 4. Restore workflow steps (reset running status to pending)
      if (session.workflowSteps && session.workflowSteps.length > 0) {
        setWorkflowSteps(session.workflowSteps.map((s: any) => ({
          ...s,
          status: s.status === 'running' ? 'pending' : s.status,
        })))
        setCenterTab('workflow')  // Switch to workflow tab
        console.log(`Restored ${session.workflowSteps.length} workflow steps`)
      }

      toast.success(`✅ Restored session: ${session.name} (${session.messageCount} messages, ${session.stepCount || 0} steps)`)
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

  const handleUpdateSkill = (skillId: string, content: string) => {
    const updated = allSkills.map((s) =>
      s.id === skillId ? { ...s, content } : s
    )

    try {
      localStorage.setItem('jmAgent:workspace:skills', JSON.stringify(updated))
    } catch (e) {
      console.error('Failed to save skills to localStorage:', e)
      toast.error('Failed to update skill')
      return
    }

    setAllSkills(updated)
    toast.success('Skill updated ✅')
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

    // 새 단계 추가 (현재 선택된 컨텍스트 파일과 스킬 스냅샷)
    const step = {
      id: Date.now().toString(),
      instruction: newStepInput,
      status: 'pending' as const,
      contextFiles: [...contextFiles],  // 스냅샷: 현재 선택된 컨텍스트 파일들
      skills: [...selectedSkills],       // 스냅샷: 현재 선택된 스킬들
    }
    setWorkflowSteps([...workflowSteps, step])
    setNewStepInput('')
    toast.success(`✅ Step added (${contextFiles.length} context, ${selectedSkills.length} skills)`)
  }


  const handleRemoveWorkflowStep = (stepId: string) => {
    setWorkflowSteps(workflowSteps.filter((s) => s.id !== stepId))
  }

  const handleUpdateWorkflowStep = (stepId: string, instruction: string) => {
    setWorkflowSteps(workflowSteps.map((s) =>
      s.id === stepId ? { ...s, instruction } : s
    ))
    toast.success('Step updated')
  }

  const handleRemoveStepContext = (stepId: string, filePath: string) => {
    setWorkflowSteps(workflowSteps.map((s) =>
      s.id === stepId
        ? { ...s, contextFiles: (s.contextFiles || []).filter((f) => f.path !== filePath) }
        : s
    ))
  }

  const handleRemoveStepSkill = (stepId: string, skillId: string) => {
    setWorkflowSteps(workflowSteps.map((s) =>
      s.id === stepId
        ? { ...s, skills: (s.skills || []).filter((sk) => sk.id !== skillId) }
        : s
    ))
  }

  const handleToggleStepDependency = (stepId: string, depStepId: string) => {
    setWorkflowSteps((prev) =>
      prev.map((s) => {
        if (s.id !== stepId) return s
        const deps = s.dependsOn || []
        const has = deps.includes(depStepId)
        return { ...s, dependsOn: has ? deps.filter((d) => d !== depStepId) : [...deps, depStepId] }
      })
    )
  }

  // 단일 step 실행 (워크플로우 전체 실행 및 re-run 공용)
  const executeStep = async (
    step: typeof workflowSteps[0],
    completedStepFiles: Record<string, string[]>,
  ): Promise<{ executionTime: number; inputTokens: number; outputTokens: number }> => {
    // Update step status to running
    setWorkflowSteps((prev) =>
      prev.map((s) =>
        s.id === step.id ? { ...s, status: 'running' as const, streamingContent: '' } : s
      )
    )
    setStreamProgress((prev) => [...prev, `▶️  Running: ${step.instruction}`])

    // 단계별 컨텍스트만 사용 (전역 fallback 없음)
    let stepContextFiles = [...(step.contextFiles || [])]

    // dependsOn: 이전 step의 생성 파일을 컨텍스트에 주입
    if (step.dependsOn && step.dependsOn.length > 0) {
      for (const depId of step.dependsOn) {
        const depFiles = completedStepFiles[depId]
        if (!depFiles) continue
        for (const filePath of depFiles) {
          if (stepContextFiles.some((f) => f.path === filePath)) continue
          try {
            const response = await filesApi.readFile(filePath)
            stepContextFiles.push({ path: filePath, content: response.content })
            setStreamProgress((prev) => [...prev, `  📎 Injected: ${filePath.split('/').pop()}`])
          } catch {
            setStreamProgress((prev) => [...prev, `  ⚠️ Failed to load: ${filePath}`])
          }
        }
      }
    }

    // 단계별 스킬만 사용 (전역 fallback 없음)
    const stepSkills = step.skills || []

    // 스킬 프리픽스 build
    const cleanSkillContent = (content: string): string => {
      let cleaned = content.replace(/## 📤 출력 형식[\s\S]*?(?=\n## |$)/, '')
      cleaned = cleaned.replace(/\[FILE_CREATE:[\s\S]*?\]/g, '')
      cleaned = cleaned.replace(/Each file MUST be wrapped in \[FILE_CREATE[\s\S]*?multiple files/g, '')
      return cleaned.trim()
    }

    let skillPrefix = ''
    if (stepSkills.length > 0) {
      const selectedSkillContents = stepSkills
        .map((selected) => {
          const skillDef = allSkills.find((s) => s.id === selected.id)
          return skillDef ? cleanSkillContent(skillDef.content) : ''
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

    const fileFormatInstruction = `

[OUTPUT FORMAT - MANDATORY]
파일 출력 시 반드시 아래 구분자를 사용하세요. 마크다운 코드블록(\`\`\`)은 사용하지 마세요.

===FILE:파일명.확장자===
파일 전체 내용 (줄바꿈 그대로, 이스케이프 없이)
===END_FILE===

`
    const stepMessage = skillPrefix + contextPrefix + step.instruction + fileFormatInstruction
    const stepConversationId = `workflow-${Date.now()}-${step.id}`

    const stepIndex = workflowSteps.findIndex(s => s.id === step.id) + 1

    const result = await sendChatStream({
      message: stepMessage,
      conversation_id: stepConversationId,
      model,
      max_tokens: 8192,
    }, (progressMsg) => {
      setStreamProgress((prev) => [...prev, `  [Step ${stepIndex}] ${progressMsg}`])
    }, (accumulated) => {
      setWorkflowSteps((prev) =>
        prev.map((s) => s.id === step.id ? { ...s, streamingContent: accumulated } : s)
      )
    })

    if (!result) {
      throw new Error('Stream cancelled')
    }

    const { content, stats } = result

    console.log(`\n📋 Step ${stepIndex} - Claude response received`)
    console.log(`Response length: ${content.length} bytes`)

    const { codeBlocks, cleanContent } = extractCodeBlocks(content)
    let createdFilePaths: string[] = []

    if (codeBlocks.length > 0) {
      setOutputBlocks(codeBlocks)
      setRightTab('output')

      if (projectRoot) {
        for (const block of codeBlocks) {
          try {
            console.log(`💾 [Auto-save] ${block.suggestedFilename}`)
            await filesApi.writeFile(block.suggestedFilename, block.code, true)
            createdFilePaths.push(block.suggestedFilename)
            setStreamProgress((prev) => [...prev, `💾 Saved: ${block.suggestedFilename}`])
          } catch (error) {
            console.error(`Failed to auto-save ${block.suggestedFilename}:`, error)
            setStreamProgress((prev) => [...prev, `⚠️ Failed to save: ${block.suggestedFilename}`])
          }
        }
        try {
          const filesRes = await filesApi.listFiles('')
          setFiles(filesRes.files || [])
        } catch (e) {
          console.error('Failed to refresh file tree:', e)
        }
      }
    }

    const finalContent = cleanContent || content

    setWorkflowSteps((prev) =>
      prev.map((s) =>
        s.id === step.id
          ? { ...s, status: 'done' as const, result: finalContent, createdFiles: createdFilePaths, streamingContent: undefined }
          : s
      )
    )

    if (createdFilePaths.length > 0) {
      completedStepFiles[step.id] = createdFilePaths
    }

    setStreamProgress((prev) => [...prev, `✅ Complete: ${step.instruction}`])

    return {
      executionTime: stats?.executionTime || 0,
      inputTokens: stats?.tokensUsed.input || 0,
      outputTokens: stats?.tokensUsed.output || 0,
    }
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

    const completedStepFiles: Record<string, string[]> = {}

    try {
      for (const step of workflowSteps) {
        try {
          const result = await executeStep(step, completedStepFiles)
          totalExecutionTime += result.executionTime
          totalInputTokens += result.inputTokens
          totalOutputTokens += result.outputTokens
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : 'Unknown error'
          console.error('Workflow step error:', error)
          setStreamProgress((prev) => [...prev, `❌ Failed: ${step.instruction} — ${errorMsg}`])
          toast.error(`Step ${workflowSteps.findIndex(s => s.id === step.id) + 1} failed: ${errorMsg}`)
          setWorkflowSteps((prev) =>
            prev.map((s) =>
              s.id === step.id ? { ...s, status: 'error' as const, result: errorMsg, streamingContent: undefined } : s
            )
          )
        }
      }

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

  const handleRerunStep = async (stepId: string) => {
    const step = workflowSteps.find((s) => s.id === stepId)
    if (!step) return

    setIsWorkflowRunning(true)
    setStreamProgress([])
    setStreamStats(null)
    setIsStreaming(true)

    // 이전 step들의 createdFiles를 수집 (dependsOn 해결용)
    const completedStepFiles: Record<string, string[]> = {}
    for (const s of workflowSteps) {
      if (s.id === stepId) break
      if (s.createdFiles && s.createdFiles.length > 0) {
        completedStepFiles[s.id] = s.createdFiles
      }
    }

    try {
      const result = await executeStep(step, completedStepFiles)
      setStreamStats({
        executionTime: result.executionTime,
        tokensUsed: {
          input: result.inputTokens,
          output: result.outputTokens,
          total: result.inputTokens + result.outputTokens,
        },
      })
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      setStreamProgress((prev) => [...prev, `❌ Failed: ${step.instruction} — ${errorMsg}`])
      toast.error(`Re-run failed: ${errorMsg}`)
      setWorkflowSteps((prev) =>
        prev.map((s) =>
          s.id === stepId ? { ...s, status: 'error' as const, result: errorMsg, streamingContent: undefined } : s
        )
      )
    } finally {
      setIsStreaming(false)
      setIsWorkflowRunning(false)
    }
  }

  // Confirmation dialog for adding context from previous step
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
        workflowSteps={workflowSteps}
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
        onUpdateSkill={handleUpdateSkill}
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
        onUpdateWorkflowStep={handleUpdateWorkflowStep}
        onRemoveStepContext={handleRemoveStepContext}
        onRemoveStepSkill={handleRemoveStepSkill}
        onToggleStepDependency={handleToggleStepDependency}
        onRerunStep={handleRerunStep}
      />

      <WorkspaceRightPanel
        rightTab={rightTab}
        setRightTab={setRightTab}
        outputBlocks={outputBlocks}
        agentMdContent={agentMdContent}
        viewingFile={viewingFile}
        isEditingMode={isEditingMode}
        agentMdSaving={agentMdSaving}
        projectRoot={projectRoot}
        onCopyToClipboard={copyToClipboard}
        onSaveAllOutput={handleSaveAllOutput}
        onSaveBlock={handleSaveBlock}
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
