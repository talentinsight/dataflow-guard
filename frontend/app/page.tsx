'use client'

export default function HomePage() {
  // Realistic sample data
  const stats = {
    totalRuns: 1247,
    successRate: 94.2,
    avgDuration: '2.3m',
    activeTests: 23
  }

  const recentRuns = [
    { id: 1, name: 'Customer Data Quality', status: 'success', time: '2 min ago', duration: '1.2m' },
    { id: 2, name: 'Order Validation Suite', status: 'success', time: '15 min ago', duration: '3.1m' },
    { id: 3, name: 'Daily ETL Checks', status: 'failed', time: '1 hour ago', duration: '0.8m' },
    { id: 4, name: 'Schema Drift Detection', status: 'success', time: '2 hours ago', duration: '2.7m' },
    { id: 5, name: 'Freshness Monitor', status: 'running', time: 'Started 5m ago', duration: '—' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">DF</span>
                </div>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-gray-900">DataFlowGuard</h1>
                <p className="text-sm text-gray-500">Data Testing & Quality Assurance</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full mr-1.5"></span>
                System Healthy
              </span>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                Run Test Suite
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          
          {/* Total Runs */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Runs</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.totalRuns.toLocaleString()}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Success Rate */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Success Rate</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.successRate}%</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Average Duration */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Avg Duration</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.avgDuration}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Active Tests */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active Tests</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.activeTests}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Runs Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Test Runs</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Latest test execution results and status</p>
          </div>
          
          <ul className="divide-y divide-gray-200">
            {recentRuns.map((run) => (
              <li key={run.id} className="px-4 py-4 hover:bg-gray-50 cursor-pointer">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {run.status === 'success' && (
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      )}
                      {run.status === 'failed' && (
                        <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                      )}
                      {run.status === 'running' && (
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      )}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{run.name}</div>
                      <div className="text-sm text-gray-500">{run.time}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-500">
                      Duration: {run.duration}
                    </div>
                    
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      run.status === 'success' 
                        ? 'bg-green-100 text-green-800' 
                        : run.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {run.status === 'success' && '✓ Passed'}
                      {run.status === 'failed' && '✗ Failed'}
                      {run.status === 'running' && '⟳ Running'}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          
          <div className="bg-gray-50 px-4 py-3 text-right">
            <button className="text-sm font-medium text-blue-600 hover:text-blue-500">
              View all runs →
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Create New Test</h3>
              <p className="text-sm text-gray-500 mb-4">Build data quality tests with zero SQL</p>
              <button className="w-full bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                Start Building
              </button>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Data Sources</h3>
              <p className="text-sm text-gray-500 mb-4">Manage Snowflake and other connections</p>
              <button className="w-full bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700">
                Configure
              </button>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <h3 className="text-lg font-medium text-gray-900 mb-2">API Documentation</h3>
              <p className="text-sm text-gray-500 mb-4">Explore REST API endpoints</p>
              <button className="w-full bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700">
                View Docs
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}