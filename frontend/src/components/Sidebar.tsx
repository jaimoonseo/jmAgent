import { NavLink } from 'react-router-dom'

interface SidebarLink {
  label: string
  href: string
  icon: string
}

const sidebarLinks: SidebarLink[] = [
  { label: 'Workspace', href: '/workspace', icon: '🏗️' },
  { label: 'Dashboard', href: '/dashboard', icon: '📊' },
  { label: 'Generate Code', href: '/generate', icon: '✨' },
  { label: 'Refactor', href: '/refactor', icon: '🔧' },
  { label: 'Test Generation', href: '/test', icon: '🧪' },
  { label: 'Explain Code', href: '/explain', icon: '📖' },
  { label: 'Bug Fix', href: '/fix', icon: '🐛' },
  { label: 'Chat', href: '/chat', icon: '💬' },
  { label: 'File Browser', href: '/files', icon: '📁' },
  { label: 'Configuration', href: '/config', icon: '⚙️' },
]

export const Sidebar = () => {
  return (
    <aside className="w-64 bg-slate-50 border-r border-slate-200 h-full">
      <nav className="p-4 space-y-2">
        {sidebarLinks.map((link) => (
          <NavLink
            key={link.href}
            to={link.href}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-100 text-primary-700 font-medium'
                  : 'text-slate-600 hover:bg-slate-100'
              }`
            }
          >
            <span className="text-lg">{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
