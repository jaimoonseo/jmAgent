import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'
import { Header } from '@/components/Header'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { GeneratePage } from '@/pages/GeneratePage'
import { RefactorPage } from '@/pages/RefactorPage'
import { TestPage } from '@/pages/TestPage'
import { ExplainPage } from '@/pages/ExplainPage'
import { FixPage } from '@/pages/FixPage'
import { ChatPage } from '@/pages/ChatPage'
import { ConfigPage } from '@/pages/ConfigPage'
import { FileBrowserPage } from '@/pages/FileBrowserPage'
import { ProjectWorkspacePage } from '@/pages/ProjectWorkspacePage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ROUTES } from '@/utils/constants'

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />
  }

  return <>{children}</>
}

export const App = () => {
  const hydrate = useAuthStore((state) => state.hydrate)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  const { isAuthenticated } = useAuthStore()

  return (
    <Router>
      <div className="min-h-screen bg-slate-50">
        {isAuthenticated && <Header />}
        <div className="flex h-[calc(100vh-80px)]">
          <Routes>
            <Route path={ROUTES.LOGIN} element={<LoginPage />} />
            <Route
              path={ROUTES.DASHBOARD}
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/generate"
              element={
                <ProtectedRoute>
                  <GeneratePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/refactor"
              element={
                <ProtectedRoute>
                  <RefactorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/test"
              element={
                <ProtectedRoute>
                  <TestPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/explain"
              element={
                <ProtectedRoute>
                  <ExplainPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fix"
              element={
                <ProtectedRoute>
                  <FixPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <ChatPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={ROUTES.CONFIG}
              element={
                <ProtectedRoute>
                  <ConfigPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={ROUTES.FILES}
              element={
                <ProtectedRoute>
                  <FileBrowserPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={ROUTES.WORKSPACE}
              element={
                <ProtectedRoute>
                  <ProjectWorkspacePage />
                </ProtectedRoute>
              }
            />
            <Route path={ROUTES.NOT_FOUND} element={<NotFoundPage />} />
          </Routes>
        </div>
        <Toaster position="top-right" />
      </div>
    </Router>
  )
}

export default App
