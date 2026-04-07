import { useState, useEffect, useRef } from 'react'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useCodeAction } from '@/hooks/useCodeAction'
import type { Model, ChatMessage, ChatResponse } from '@/types/actions'

export const ChatPage = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState<string>('')
  const [model, setModel] = useState<Model>('haiku')
  const [maxTokens, setMaxTokens] = useState(4096)
  const { loading, error, execute, reset } = useCodeAction()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim()) {
      return
    }

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')

    try {
      const response = await execute({
        action: 'chat',
        params: {
          message: input,
          conversation_id: conversationId || undefined,
          model,
          max_tokens: maxTokens,
        },
      })

      const chatResponse = response as ChatResponse
      setConversationId(chatResponse.conversation_id)

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: chatResponse.response,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      // Error is already handled by the hook
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setConversationId('')
    reset()
  }

  return (
    <div className="flex-1 p-8 flex flex-col h-[calc(100vh-80px)]">
      <div className="max-w-4xl mx-auto w-full flex flex-col h-full">
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Chat with Claude</h1>
              <p className="text-slate-600 mt-1">
                Ask questions about your code or get coding assistance.
              </p>
            </div>
            {conversationId && (
              <div className="text-sm text-slate-500">
                <span className="font-mono">ID: {conversationId.substring(0, 8)}...</span>
              </div>
            )}
          </div>
        </div>

        {/* Settings Panel */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-slate-900">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value as Model)}
                disabled={messages.length > 0}
                className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-slate-100 disabled:cursor-not-allowed"
              >
                <option value="haiku">Haiku 4.5 (Fast)</option>
                <option value="sonnet">Sonnet 4.6 (Balanced)</option>
                <option value="opus">Opus 4.6 (Quality)</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-slate-900">Max Tokens</label>
              <input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                min="256"
                max="8192"
                step="256"
                disabled={messages.length > 0}
                className="px-4 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-slate-100 disabled:cursor-not-allowed"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={handleNewChat}
                className="w-full px-4 py-2 bg-slate-200 text-slate-900 font-medium rounded-lg hover:bg-slate-300 transition-colors"
              >
                New Chat
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 bg-white rounded-lg shadow p-6 overflow-y-auto mb-6 space-y-4" aria-live="polite" aria-label="Chat messages">
          {messages.length === 0 && !loading && (
            <div className="flex items-center justify-center h-full text-center">
              <div>
                <div className="text-4xl mb-4">💬</div>
                <p className="text-slate-600 mb-2">Start a conversation</p>
                <p className="text-sm text-slate-500">
                  Ask questions about code, request help, or discuss programming concepts.
                </p>
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div
              key={`${conversationId}-${message.role}-${idx}`}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white rounded-br-none'
                    : 'bg-slate-100 text-slate-900 rounded-bl-none'
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-100 text-slate-900 px-4 py-3 rounded-lg rounded-bl-none">
                <div className="flex items-center gap-2">
                  <LoadingSpinner />
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="flex justify-start">
              <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg rounded-bl-none">
                <p className="text-sm">
                  {(error.response?.data as any)?.detail ||
                    error.message ||
                    'An error occurred'}
                </p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder="Type your message... (Shift+Enter for new line)"
              disabled={loading}
              className="flex-1 p-3 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none max-h-32"
              rows={2}
            />
            <button
              onClick={handleSendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2 self-end"
            >
              {loading ? (
                <>
                  <LoadingSpinner />
                  Sending
                </>
              ) : (
                'Send'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
