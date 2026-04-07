import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigPage } from '@/pages/ConfigPage'
import { useAuthStore } from '@/store/authStore'
import * as api from '@/utils/api'
import toast from 'react-hot-toast'

vi.mock('@/store/authStore')
vi.mock('@/utils/api')
vi.mock('react-hot-toast')

const mockConfig = {
  jm_default_model: 'haiku',
  jm_temperature: 0.2,
  jm_max_tokens: 4096,
  jm_enable_caching: true,
  jm_log_level: 'INFO',
  host: 'localhost',
  port: 8000,
  debug: false,
}

const renderConfigPage = () => {
  return render(
    <BrowserRouter>
      <ConfigPage />
    </BrowserRouter>
  )
}

describe('ConfigPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders ConfigPage with loading spinner while fetching', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockReturnValue(
      new Promise((resolve) => setTimeout(() => resolve(mockConfig), 100))
    )

    renderConfigPage()

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('displays all settings from API after loading', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)

    renderConfigPage()

    await waitFor(() => {
      expect(screen.getByDisplayValue('haiku')).toBeInTheDocument()
      expect(screen.getByDisplayValue('0.2')).toBeInTheDocument()
      expect(screen.getByDisplayValue('4096')).toBeInTheDocument()
    })
  })

  it('updates a single setting and shows success toast', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)
    vi.mocked(api.updateConfigSetting).mockResolvedValue({
      ...mockConfig,
      jm_temperature: 0.5,
    })

    renderConfigPage()

    await waitFor(() => {
      expect(screen.getByDisplayValue('0.2')).toBeInTheDocument()
    })

    const temperatureInput = screen.getByDisplayValue('0.2') as HTMLInputElement
    fireEvent.change(temperatureInput, { target: { value: '0.5' } })
    fireEvent.blur(temperatureInput)

    await waitFor(() => {
      expect(api.updateConfigSetting).toHaveBeenCalledWith('jm_temperature', 0.5)
      expect(toast.success).toHaveBeenCalled()
    })
  })

  it('shows error toast on failed update', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)
    vi.mocked(api.updateConfigSetting).mockRejectedValue(new Error('Update failed'))

    renderConfigPage()

    await waitFor(() => {
      expect(screen.getByDisplayValue('0.2')).toBeInTheDocument()
    })

    const temperatureInput = screen.getByDisplayValue('0.2') as HTMLInputElement
    fireEvent.change(temperatureInput, { target: { value: '0.5' } })
    fireEvent.blur(temperatureInput)

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled()
    })
  })

  it('displays reset button for admin users', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)

    renderConfigPage()

    await waitFor(() => {
      expect(screen.getByText(/reset all settings/i)).toBeInTheDocument()
    })
  })

  it('hides reset button for non-admin users', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'user', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)

    renderConfigPage()

    await waitFor(() => {
      expect(screen.queryByText(/reset all settings/i)).not.toBeInTheDocument()
    })
  })

  it('handles reset button click for admin users', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)
    vi.mocked(api.resetAllSettings).mockResolvedValue({
      message: 'Settings reset',
      config: mockConfig,
    })

    renderConfigPage()

    await waitFor(() => {
      expect(screen.getByText(/reset all settings/i)).toBeInTheDocument()
    })

    const resetButton = screen.getByText(/reset all settings/i)
    fireEvent.click(resetButton)

    await waitFor(() => {
      expect(api.resetAllSettings).toHaveBeenCalled()
      expect(toast.success).toHaveBeenCalled()
    })
  })

  it('renders different field types correctly', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)

    renderConfigPage()

    await waitFor(() => {
      // String field
      expect(screen.getByDisplayValue('haiku')).toBeInTheDocument()
      // Number field
      expect(screen.getByDisplayValue('0.2')).toBeInTheDocument()
      // At minimum we should have string and number fields rendered
      expect(screen.getByText('Default Model')).toBeInTheDocument()
      expect(screen.getByText('Temperature')).toBeInTheDocument()
    })
  })

  it('handles fetch error gracefully', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', role: 'admin', email: 'test@example.com' },
      isAuthenticated: true,
      token: 'token',
      apiKey: null,
      login: vi.fn(),
      loginWithApiKey: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      hydrate: vi.fn(),
    })

    vi.mocked(api.getConfig).mockRejectedValue(new Error('Fetch failed'))

    renderConfigPage()

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
    })
  })
})
