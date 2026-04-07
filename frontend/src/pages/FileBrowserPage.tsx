import { useState, useEffect } from 'react'
import { filesApi } from '@/api/endpoints'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import type { FileInfo, FileListResponse } from '@/types/files'
import toast from 'react-hot-toast'

interface FileTreeNodeProps {
  file: FileInfo
  onSelectFile: (path: string) => void
  level: number
}

const FileTreeNode = ({ file, onSelectFile, level }: FileTreeNodeProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [children, setChildren] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(false)

  const handleToggle = async () => {
    if (file.type === 'directory') {
      if (!isOpen && children.length === 0) {
        setLoading(true)
        try {
          const response = await filesApi.listFiles(file.path)
          const data = response as FileListResponse
          setChildren(data.files || [])
        } catch (error) {
          toast.error(`Failed to load ${file.name}`)
        } finally {
          setLoading(false)
        }
      }
      setIsOpen(!isOpen)
    } else {
      onSelectFile(file.path)
    }
  }

  const icon = file.type === 'directory' ? (isOpen ? '📂' : '📁') : '📄'
  const paddingLeft = `${level * 16}px`

  return (
    <div>
      <div
        onClick={handleToggle}
        className="flex items-center gap-2 py-1 px-2 hover:bg-slate-100 cursor-pointer rounded"
        style={{ paddingLeft }}
      >
        <span className="w-4">{file.type === 'directory' ? (isOpen ? '▼' : '▶') : ''}</span>
        <span className="text-lg">{icon}</span>
        <span className="text-sm text-slate-900">{file.name}</span>
        {file.size && <span className="text-xs text-slate-500 ml-auto">({file.size} bytes)</span>}
        {loading && <LoadingSpinner />}
      </div>

      {isOpen && children.length > 0 && (
        <div>
          {children.map((child) => (
            <FileTreeNode
              key={child.path}
              file={child}
              onSelectFile={onSelectFile}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export const FileBrowserPage = () => {
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [contentLoading, setContentLoading] = useState(false)

  useEffect(() => {
    const loadRootFiles = async () => {
      try {
        const response = await filesApi.listFiles('')
        const data = response as FileListResponse
        setFiles(data.files || [])
      } catch (error) {
        toast.error('Failed to load project files')
      } finally {
        setLoading(false)
      }
    }

    loadRootFiles()
  }, [])

  const handleSelectFile = async (path: string) => {
    setSelectedFile(path)
    setContentLoading(true)
    try {
      const response = await filesApi.readFile(path)
      setFileContent(response.content || '')
    } catch (error) {
      toast.error('Failed to read file')
      setFileContent('')
    } finally {
      setContentLoading(false)
    }
  }

  return (
    <div className="flex-1 p-8 flex flex-col h-[calc(100vh-80px)]">
      <div className="max-w-6xl mx-auto w-full flex flex-col h-full gap-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900">File Browser</h1>
          <p className="text-slate-600 mt-1">Browse and edit project files</p>
        </div>

        {/* Main Content */}
        <div className="flex gap-6 flex-1 min-h-0">
          {/* File Tree */}
          <div className="w-80 bg-white rounded-lg shadow p-4 overflow-y-auto">
            <h2 className="font-bold text-slate-900 mb-4">Project Files</h2>
            {loading ? (
              <LoadingSpinner />
            ) : files.length === 0 ? (
              <p className="text-slate-500 text-sm">No files found</p>
            ) : (
              <div>
                {files.map((file) => (
                  <FileTreeNode
                    key={file.path}
                    file={file}
                    onSelectFile={handleSelectFile}
                    level={0}
                  />
                ))}
              </div>
            )}
          </div>

          {/* File Content */}
          <div className="flex-1 bg-white rounded-lg shadow p-4 overflow-y-auto flex flex-col">
            {selectedFile ? (
              <>
                <div className="mb-4 pb-4 border-b">
                  <h3 className="font-mono text-sm text-slate-900">{selectedFile}</h3>
                </div>

                {contentLoading ? (
                  <LoadingSpinner />
                ) : (
                  <pre className="flex-1 bg-slate-50 p-4 rounded font-mono text-sm overflow-auto text-slate-900 whitespace-pre-wrap break-words">
                    {fileContent}
                  </pre>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400">
                <p>Select a file to view its contents</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
