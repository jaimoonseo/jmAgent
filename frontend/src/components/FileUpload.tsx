import { ChangeEvent, DragEvent, KeyboardEvent, useRef, useState } from 'react'
import toast from 'react-hot-toast'

interface FileUploadProps {
  onFileSelected: (content: string, fileName: string) => void
  accept?: string
  maxSize?: number
}

export const FileUpload = ({
  onFileSelected,
  accept = '.py,.ts,.js,.sql,.sh,.json,.yaml,.yml',
  maxSize = 1048576, // 1MB
}: FileUploadProps) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [fileName, setFileName] = useState<string | null>(null)

  const handleFile = (file: File) => {
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${maxSize / 1024 / 1024}MB`)
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      onFileSelected(content, file.name)
      setFileName(file.name)
      toast.success(`File "${file.name}" uploaded successfully`)
    }
    reader.onerror = () => {
      toast.error('Failed to read file')
    }
    reader.readAsText(file)
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      inputRef.current?.click()
    }
  }

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={handleKeyDown}
        role="button"
        aria-label="Upload code file - drag and drop or click"
        tabIndex={0}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-slate-300 bg-slate-50 hover:border-slate-400'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          onChange={handleChange}
          accept={accept}
          className="hidden"
        />
        <div className="text-slate-600" onClick={() => inputRef.current?.click()}>
          <div className="text-2xl mb-2">📁</div>
          <p className="text-sm font-medium">
            {fileName ? `Selected: ${fileName}` : 'Drag and drop your file here'}
          </p>
          <p className="text-xs text-slate-500 mt-1">or click to browse</p>
          <p className="text-xs text-slate-400 mt-2">
            Supported: {accept.split(',').join(', ')}
          </p>
        </div>
      </div>
    </div>
  )
}
