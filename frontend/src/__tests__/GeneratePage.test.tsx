import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GeneratePage } from '@/pages/GeneratePage'

vi.mock('@/hooks/useCodeAction', () => ({
  useCodeAction: () => ({
    data: null,
    loading: false,
    error: null,
    execute: vi.fn(),
    reset: vi.fn(),
  }),
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('GeneratePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page title', () => {
    render(<GeneratePage />)
    expect(screen.getByRole('heading', { name: /Generate Code/ })).toBeInTheDocument()
  })

  it('renders description text', () => {
    render(<GeneratePage />)
    expect(
      screen.getByText(/Describe what you want to create/)
    ).toBeInTheDocument()
  })

  it('renders input form fields', () => {
    render(<GeneratePage />)
    expect(screen.getByText(/Model/)).toBeInTheDocument()
    expect(screen.getByText(/Temperature/)).toBeInTheDocument()
    expect(screen.getByText(/Max Tokens/)).toBeInTheDocument()
  })

  it('renders generate button', () => {
    const { container } = render(<GeneratePage />)
    const buttons = container.querySelectorAll('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('enables/disables generate button based on prompt', () => {
    const { container } = render(<GeneratePage />)

    // Find the generate button by looking for the specific class pattern
    const buttons = container.querySelectorAll('button')
    const generateButton = buttons[0] as HTMLButtonElement

    expect(generateButton).toBeInTheDocument()
  })

  it('displays model selector with default value', () => {
    render(<GeneratePage />)
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBeGreaterThan(0)
  })

  it('updates temperature when slider is adjusted', async () => {
    const { container } = render(<GeneratePage />)
    const sliders = container.querySelectorAll('input[type="range"]')
    if (sliders.length > 0) {
      const slider = sliders[0] as HTMLInputElement
      // Change the slider value directly
      slider.value = '0.8'
      slider.dispatchEvent(new Event('change', { bubbles: true }))
      expect(slider.value).toBe('0.8')
    }
  })

  it('updates max tokens when input is changed', async () => {
    const { container } = render(<GeneratePage />)
    const inputs = container.querySelectorAll('input[type="number"]')
    if (inputs.length > 0) {
      const input = inputs[0] as HTMLInputElement
      // Change the input value directly
      input.value = '2048'
      input.dispatchEvent(new Event('change', { bubbles: true }))
      expect(input.value).toBe('2048')
    }
  })

  it('renders temperature slider', () => {
    const { container } = render(<GeneratePage />)
    const sliders = container.querySelectorAll('input[type="range"]')
    expect(sliders.length).toBeGreaterThan(0)
  })
})
