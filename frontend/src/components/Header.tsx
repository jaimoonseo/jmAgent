import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { APP_TITLE } from '@/utils/constants'

export const Header = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
  }

  return (
    <header className="bg-white shadow-sm border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center cursor-pointer"
            onClick={() => navigate('/dashboard')}
          >
            <span className="text-white font-bold text-lg">J</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900">{APP_TITLE}</h1>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-900">{user.name || user.email || user.id}</p>
                <p className="text-xs text-slate-500">{user.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-900 rounded-lg transition-colors text-sm font-medium"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
