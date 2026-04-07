import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ModelSelector } from '@/components/ModelSelector'

describe('ModelSelector', () => {
  it('renders with default label', () => {
    render(
      <ModelSelector value="haiku" onChange={() => {}} />
    )
    expect(screen.getByText('Model')).toBeInTheDocument()
  })

  it('renders with custom label', () => {
    render(
      <ModelSelector
        value="haiku"
        onChange={() => {}}
        label="AI Model"
      />
    )
    expect(screen.getByText('AI Model')).toBeInTheDocument()
  })

  it('displays all model options', () => {
    render(
      <ModelSelector value="haiku" onChange={() => {}} />
    )
    expect(screen.getByText(/Haiku 4.5/)).toBeInTheDocument()
    expect(screen.getByText(/Sonnet 4.6/)).toBeInTheDocument()
    expect(screen.getByText(/Opus 4.6/)).toBeInTheDocument()
  })

  it('renders with selected value', () => {
    const { container } = render(
      <ModelSelector value="sonnet" onChange={() => {}} />
    )
    const select = container.querySelector('select') as HTMLSelectElement
    expect(select.value).toBe('sonnet')
  })

  it('calls onChange when model is changed', async () => {
    const user = userEvent.setup()
    const handleChange = vi.fn()
    const { container } = render(
      <ModelSelector value="haiku" onChange={handleChange} />
    )

    const select = container.querySelector('select') as HTMLSelectElement
    await user.selectOptions(select, 'opus')

    expect(handleChange).toHaveBeenCalledWith('opus')
  })

  it('disables select when disabled prop is true', () => {
    const { container } = render(
      <ModelSelector
        value="haiku"
        onChange={() => {}}
        disabled={true}
      />
    )
    const select = container.querySelector('select') as HTMLSelectElement
    expect(select.disabled).toBe(true)
  })

  it('applies disabled styling', () => {
    const { container } = render(
      <ModelSelector
        value="haiku"
        onChange={() => {}}
        disabled={true}
      />
    )
    const select = container.querySelector('select')
    expect(select?.className).toContain('disabled:bg-slate-100')
  })
})
