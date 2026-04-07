import { useAuth } from '@/hooks/useAuth'
import { Sidebar } from '@/components/Sidebar'

export const DashboardPage = () => {
  const { user } = useAuth()

  return (
    <div className="flex h-full">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Welcome back, {user?.name || user?.id}!</h1>
          <p className="text-slate-600">Choose an action from the sidebar to get started.</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-slate-600 mb-2">Total Generations</div>
            <div className="text-3xl font-bold text-slate-900">0</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-slate-600 mb-2">Total Refactors</div>
            <div className="text-3xl font-bold text-slate-900">0</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-slate-600 mb-2">Total Tests</div>
            <div className="text-3xl font-bold text-slate-900">0</div>
          </div>
        </div>

        {/* Features Overview */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 transition-colors cursor-pointer">
              <div className="text-2xl mb-2">✨</div>
              <h3 className="font-semibold text-slate-900">Generate Code</h3>
              <p className="text-sm text-slate-600 mt-1">Generate code snippets from natural language descriptions.</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 transition-colors cursor-pointer">
              <div className="text-2xl mb-2">🔧</div>
              <h3 className="font-semibold text-slate-900">Refactor Code</h3>
              <p className="text-sm text-slate-600 mt-1">Improve existing code with AI-powered refactoring.</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 transition-colors cursor-pointer">
              <div className="text-2xl mb-2">🧪</div>
              <h3 className="font-semibold text-slate-900">Generate Tests</h3>
              <p className="text-sm text-slate-600 mt-1">Automatically generate comprehensive unit tests.</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 transition-colors cursor-pointer">
              <div className="text-2xl mb-2">📖</div>
              <h3 className="font-semibold text-slate-900">Explain Code</h3>
              <p className="text-sm text-slate-600 mt-1">Get detailed explanations of any code snippet.</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 transition-colors cursor-pointer">
              <div className="text-2xl mb-2">🐛</div>
              <h3 className="font-semibold text-slate-900">Fix Bugs</h3>
              <p className="text-sm text-slate-600 mt-1">Identify and fix bugs with AI assistance.</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 transition-colors cursor-pointer">
              <div className="text-2xl mb-2">💬</div>
              <h3 className="font-semibold text-slate-900">Interactive Chat</h3>
              <p className="text-sm text-slate-600 mt-1">Chat with Claude about your code questions.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
