import { useEffect, useRef } from 'react'
import hljs from 'highlight.js'
import toast from 'react-hot-toast'
import 'highlight.js/styles/atom-one-dark.css'

interface CodeOutputProps {
  code: string
  language?: string
  showLanguageLabel?: boolean
  showCopyButton?: boolean
}

export const CodeOutput = ({
  code,
  language = 'plaintext',
  showLanguageLabel = true,
  showCopyButton = true,
}: CodeOutputProps) => {
  const codeRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (codeRef.current) {
      codeRef.current.innerText = code
      hljs.highlightElement(codeRef.current)
    }
  }, [code, language])

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      toast.success('Code copied to clipboard!')
    })
  }

  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden border border-slate-700">
      <div className="flex items-center justify-between bg-slate-950 px-4 py-3 border-b border-slate-700">
        {showLanguageLabel && (
          <span className="text-xs text-slate-400 font-mono uppercase">
            {language}
          </span>
        )}
        {showCopyButton && (
          <button
            onClick={handleCopy}
            className="ml-auto px-3 py-1 text-xs text-slate-300 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
          >
            Copy
          </button>
        )}
      </div>
      <pre className="p-4 overflow-auto max-h-96">
        <code
          ref={codeRef}
          className={`language-${language}`}
        >
          {code}
        </code>
      </pre>
    </div>
  )
}
