import { ChangeEvent } from 'react'

interface CodeEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  placeholder?: string
  height?: string
  readOnly?: boolean
}

export const CodeEditor = ({
  value,
  onChange,
  language = 'plaintext',
  placeholder = 'Enter code here...',
  height = 'h-64',
  readOnly = false,
}: CodeEditorProps) => {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  return (
    <div className="flex flex-col gap-2">
      {language !== 'plaintext' && (
        <div className="text-xs text-slate-500 font-mono">
          Language: {language}
        </div>
      )}
      <textarea
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`${height} w-full p-4 bg-slate-900 text-slate-100 border border-slate-700 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none ${
          readOnly ? 'cursor-not-allowed bg-slate-950' : ''
        }`}
      />
    </div>
  )
}
