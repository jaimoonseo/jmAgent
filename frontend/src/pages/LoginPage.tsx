import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { APP_TITLE } from '@/utils/constants'

type AuthMethod = 'token' | 'apiKey'

export const LoginPage = () => {
  const { loginWithToken, loginWithApiKey, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [method, setMethod] = useState<AuthMethod>('token')
  const [loading, setLoading] = useState(false)
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  // Redirect to dashboard if already authenticated
  // Note: sessionStorage is cleared when browser closes, so user will need to login again next session
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (method === 'token') {
        await loginWithToken(value)
      } else {
        await loginWithApiKey(value)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <div className="w-12 h-12 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-2xl">J</span>
            </div>
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-center text-slate-900 mb-2">{APP_TITLE}</h1>
          <p className="text-center text-slate-600 text-sm mb-8">Sign in to your account</p>

          {/* Tabs */}
          <div className="flex gap-2 mb-8 border-b border-slate-200">
            <button
              onClick={() => {
                setMethod('token')
                setValue('')
                setError('')
              }}
              className={`flex-1 py-2 font-medium text-sm transition-colors ${
                method === 'token'
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              JWT Token
            </button>
            <button
              onClick={() => {
                setMethod('apiKey')
                setValue('')
                setError('')
              }}
              className={`flex-1 py-2 font-medium text-sm transition-colors ${
                method === 'apiKey'
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              API Key
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                {method === 'token' ? 'JWT Bearer Token' : 'API Key'}
              </label>
              <textarea
                value={value}
                onChange={(e) => {
                  setValue(e.target.value)
                  setError('')
                }}
                placeholder={method === 'token' ? 'eyJhbGc...' : 'sk-...'}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm font-mono"
                rows={4}
                disabled={loading}
              />
            </div>

            {/* Error Message */}
            {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !value.trim()}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 text-white font-medium py-2.5 rounded-lg transition-colors"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-slate-600 text-xs mt-6">
            For development, use a valid token from the jmAgent backend API.
          </p>
        </div>
      </div>
    </div>
  )
}
