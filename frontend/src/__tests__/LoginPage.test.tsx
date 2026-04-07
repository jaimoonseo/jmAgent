import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from '@/pages/LoginPage'
import { useAuthStore } from '@/store/authStore'

vi.mock('@/api/endpoints', () => ({
  authApi: {
    validateToken: vi.fn(),
    validateApiKey: vi.fn(),
  },
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: null,
      apiKey: null,
      isAuthenticated: false,
      user: null,
    })
  })

  it('should render login form', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText('jmAgent Web Dashboard')).toBeDefined()
    expect(screen.getByPlaceholderText('eyJhbGc...')).toBeDefined()
  })

  it('should switch between JWT and API Key tabs', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const apiKeyTab = screen.getByText('API Key')
    fireEvent.click(apiKeyTab)

    expect(screen.getByPlaceholderText('sk-...')).toBeDefined()
  })

  it('should disable submit button when input is empty', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByText('Sign In') as HTMLButtonElement
    expect(submitButton.disabled).toBe(true)
  })

  it('should enable submit button when input has value', async () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const textarea = screen.getByPlaceholderText('eyJhbGc...') as HTMLTextAreaElement
    const submitButton = screen.getByText('Sign In') as HTMLButtonElement

    fireEvent.change(textarea, { target: { value: 'test-token' } })

    await waitFor(() => {
      expect(submitButton.disabled).toBe(false)
    })
  })
})
