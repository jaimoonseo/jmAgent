import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CodeEditor } from '@/components/CodeEditor'

describe('CodeEditor', () => {
  it('renders textarea with value', () => {
    const { container } = render(
      <CodeEditor
        value="const x = 5;"
        onChange={() => {}}
      />
    )
    const textarea = container.querySelector('textarea')
    expect(textarea?.value).toBe('const x = 5;')
  })

  it('renders with custom placeholder', () => {
    const { container } = render(
      <CodeEditor
        value=""
        onChange={() => {}}
        placeholder="Enter code here"
      />
    )
    const textarea = container.querySelector('textarea')
    expect(textarea?.placeholder).toBe('Enter code here')
  })

  it('renders language label when language is not plaintext', () => {
    render(
      <CodeEditor
        value=""
        onChange={() => {}}
        language="python"
      />
    )
    expect(screen.getByText(/Language: python/)).toBeInTheDocument()
  })

  it('calls onChange when text is typed', async () => {
    const user = userEvent.setup()
    const handleChange = vi.fn()
    const { container } = render(
      <CodeEditor
        value=""
        onChange={handleChange}
      />
    )
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement
    await user.type(textarea, 'console.log("test")')
    expect(handleChange).toHaveBeenCalled()
  })

  it('applies readOnly class when readOnly prop is true', () => {
    const { container } = render(
      <CodeEditor
        value="const x = 5;"
        onChange={() => {}}
        readOnly={true}
      />
    )
    const textarea = container.querySelector('textarea')
    expect(textarea?.readOnly).toBe(true)
    expect(textarea?.className).toContain('cursor-not-allowed')
  })

  it('applies custom height class', () => {
    const { container } = render(
      <CodeEditor
        value=""
        onChange={() => {}}
        height="h-96"
      />
    )
    const textarea = container.querySelector('textarea')
    expect(textarea?.className).toContain('h-96')
  })
})
