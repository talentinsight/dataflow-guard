'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { 
  LayoutDashboard, 
  Play, 
  TestTube, 
  Database, 
  Settings,
  Zap
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, shortcut: 'g d' },
  { name: 'Runs', href: '/runs', icon: Play, shortcut: 'g r' },
  { name: 'Test Builder', href: '/builder', icon: TestTube, shortcut: 'g b' },
  { name: 'Datasets', href: '/datasets', icon: Database, shortcut: 'g s' },
  { name: 'Settings', href: '/settings', icon: Settings, shortcut: 'g s' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-white border-r border-gray-200 dark:bg-gray-900 dark:border-gray-800">
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">DataFlowGuard</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">Operator Console</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-gray-800 dark:text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white'
              )}
              aria-label={`${item.name} (${item.shortcut})`}
            >
              <Icon
                className={cn(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  isActive ? 'text-blue-700 dark:text-white' : 'text-gray-500 group-hover:text-gray-700 dark:text-gray-400 dark:group-hover:text-white'
                )}
              />
              {item.name}
              <span className="ml-auto text-xs text-gray-500 group-hover:text-gray-400">
                {item.shortcut}
              </span>
            </Link>
          )
        })}
      </nav>

      {/* Status */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-4">
        <div className="flex items-center space-x-2 text-sm">
          <div className="h-2 w-2 rounded-full bg-green-400"></div>
          <span className="text-gray-600 dark:text-gray-300">All Systems Operational</span>
        </div>
      </div>
    </div>
  )
}
