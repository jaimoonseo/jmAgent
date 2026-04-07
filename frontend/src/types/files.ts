/**
 * File management types for the file browser
 */

export interface FileInfo {
  /** File or directory name */
  name: string
  /** Relative path from project root */
  path: string
  /** 'file' or 'directory' */
  type: 'file' | 'directory'
  /** File size in bytes (null for directories) */
  size?: number
}

export interface FileListResponse {
  /** Current directory path */
  path: string
  /** Files and directories in the path */
  files: FileInfo[]
}

export interface FileReadResponse {
  /** File path */
  path: string
  /** File content */
  content: string
  /** File size in bytes */
  size: number
}

export interface FileWriteResponse {
  /** File path written */
  path: string
  /** Whether write was successful */
  success: boolean
  /** File size after write */
  size: number
}

export interface SetProjectRootResponse {
  /** Project root path */
  project_root: string
}
