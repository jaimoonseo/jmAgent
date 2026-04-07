import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CodeOutput } from '@/components/CodeOutput'

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('CodeOutput', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders code with language label', () => {
    render(
      <CodeOutput
        code="const x = 5;"
        language="javascript"
        showLanguageLabel={true}
      />
    )
    expect(screen.getByText(/javascript/i)).toBeInTheDocument()
  })

  it('does not show language label when showLanguageLabel is false', () => {
    render(
      <CodeOutput
        code="const x = 5;"
        language="javascript"
        showLanguageLabel={false}
      />
    )
    expect(screen.queryByText(/javascript/i)).not.toBeInTheDocument()
  })

  it('renders copy button by default', () => {
    render(
      <CodeOutput
        code="const x = 5;"
        language="javascript"
      />
    )
    expect(screen.getByText(/Copy/)).toBeInTheDocument()
  })

  it('does not render copy button when showCopyButton is false', () => {
    render(
      <CodeOutput
        code="const x = 5;"
        language="javascript"
        showCopyButton={false}
      />
    )
    expect(screen.queryByText(/Copy/)).not.toBeInTheDocument()
  })

  it('copy button is clickable', async () => {
    const user = userEvent.setup()
    render(
      <CodeOutput
        code="const x = 5;"
        language="javascript"
      />
    )

    const copyButton = screen.getByText(/Copy/)
    expect(copyButton).toBeInTheDocument()
    // Verify button can be clicked (don't test clipboard due to jsdom limitations)
    await user.click(copyButton)
  })
})
