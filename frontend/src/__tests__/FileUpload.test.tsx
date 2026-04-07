import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileUpload } from '@/components/FileUpload'

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

import toast from 'react-hot-toast'

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders drag and drop zone', () => {
    render(
      <FileUpload onFileSelected={() => {}} />
    )
    expect(screen.getByText(/Drag and drop your file here/)).toBeInTheDocument()
  })

  it('shows file input when clicked', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <FileUpload onFileSelected={() => {}} />
    )
    const dropZone = container.querySelector('[class*="border-dashed"]')
    if (dropZone) {
      await user.click(dropZone)
    }
  })

  it('calls onFileSelected with file content when file is selected', async () => {
    const user = userEvent.setup()
    const mockCallback = vi.fn()
    const { container } = render(
      <FileUpload onFileSelected={mockCallback} />
    )

    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['const x = 5;'], 'test.js', { type: 'text/plain' })

    await user.upload(input, file)

    // Wait for file to be read
    await new Promise((resolve) => setTimeout(resolve, 100))
    expect(mockCallback).toHaveBeenCalledWith('const x = 5;', 'test.js')
  })

  it('shows error toast when file is too large', async () => {
    const user = userEvent.setup()
    vi.mocked(toast.error).mockImplementation(() => 'test')
    const mockCallback = vi.fn()
    const { container } = render(
      <FileUpload onFileSelected={mockCallback} maxSize={100} />
    )

    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    const largeContent = 'x'.repeat(200)
    const file = new File([largeContent], 'large.js', { type: 'text/plain' })

    await user.upload(input, file)

    expect(toast.error).toHaveBeenCalledWith(expect.stringContaining('File size'))
  })

  it('shows file name after selection', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <FileUpload onFileSelected={() => {}} />
    )

    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'mycode.py', { type: 'text/plain' })

    await user.upload(input, file)

    // Wait for file to be read and displayed
    await new Promise((resolve) => setTimeout(resolve, 100))
    expect(screen.getByText(/Selected: mycode.py/)).toBeInTheDocument()
  })

  it('displays supported file types', () => {
    render(
      <FileUpload
        onFileSelected={() => {}}
        accept=".py,.ts,.js"
      />
    )
    expect(screen.getByText(/Supported:/)).toBeInTheDocument()
  })
})
