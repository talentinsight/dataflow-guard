'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useWorkspaceStore } from '@/stores/workspace'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState } from '@/components/common/EmptyState'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { CheckCircle, XCircle, AlertTriangle, Download, FileText, BarChart3 } from 'lucide-react'

export function ResultsPanel() {
  const { runId, status } = useWorkspaceStore()
  const [activeTab, setActiveTab] = useState('summary')

  // Query for run results
  const { data: results, isLoading } = useQuery({
    queryKey: ['run-results', runId],
    queryFn: () => runId ? apiClient.getRunResults(runId) : null,
    enabled: !!runId && (status === 'done' || status === 'error'),
    retry: false,
  })

  // Mock results for demonstration
  const mockResults = {
    summary: {
      total_tests: 8,
      passed: 6,
      failed: 1,
      errors: 1,
      execution_time_ms: 4250,
      data_scanned_bytes: 1024000
    },
    test_results: [
      { id: 'null-check', name: 'Null Value Check', status: 'pass', duration_ms: 450, violations: 0 },
      { id: 'duplicate-check', name: 'Duplicate Detection', status: 'pass', duration_ms: 680, violations: 0 },
      { id: 'range-check', name: 'Value Range Validation', status: 'fail', duration_ms: 320, violations: 15 },
      { id: 'type-check', name: 'Data Type Validation', status: 'pass', duration_ms: 290, violations: 0 },
      { id: 'constraint-check', name: 'Constraint Validation', status: 'pass', duration_ms: 520, violations: 0 },
      { id: 'column-check', name: 'Column Existence', status: 'pass', duration_ms: 180, violations: 0 },
      { id: 'last-update', name: 'Last Update Check', status: 'error', duration_ms: 0, error: 'Connection timeout' },
      { id: 'batch-freshness', name: 'Batch Freshness', status: 'pass', duration_ms: 410, violations: 0 },
    ]
  }

  const displayResults = results || (status !== 'idle' ? mockResults : null)

  // Chart data
  const statusData = displayResults ? [
    { name: 'Passed', value: displayResults.summary.passed, color: '#22c55e' },
    { name: 'Failed', value: displayResults.summary.failed, color: '#ef4444' },
    { name: 'Errors', value: displayResults.summary.errors, color: '#f59e0b' },
  ].filter(item => item.value > 0) : []

  const durationData = displayResults?.test_results.map((test: any) => ({
    name: test.name.split(' ')[0], // Shortened name for chart
    duration: test.duration_ms,
    status: test.status
  })) || []

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'fail':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      pass: 'bg-green-100 text-green-800',
      fail: 'bg-red-100 text-red-800',
      error: 'bg-yellow-100 text-yellow-800'
    }
    return variants[status as keyof typeof variants] || 'bg-gray-100 text-gray-800'
  }

  if (!displayResults) {
    return (
      <Card className="h-full">
        <CardContent className="h-full flex items-center justify-center">
          <EmptyState
            icon={<BarChart3 className="h-12 w-12" />}
            title="No results yet"
            description="Run tests to see results and metrics"
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <div>
              <CardTitle className="text-base">Test Results</CardTitle>
              <CardDescription className="text-sm">
                {displayResults.summary.total_tests} tests • {displayResults.summary.execution_time_ms}ms
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-3 w-3" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="details">Test Details</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
          </TabsList>
          
          <TabsContent value="summary" className="flex-1 space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Test Status</h4>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center space-x-2">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      <span>Passed</span>
                    </span>
                    <span className="font-medium">{displayResults.summary.passed}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center space-x-2">
                      <XCircle className="h-3 w-3 text-red-500" />
                      <span>Failed</span>
                    </span>
                    <span className="font-medium">{displayResults.summary.failed}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center space-x-2">
                      <AlertTriangle className="h-3 w-3 text-yellow-500" />
                      <span>Errors</span>
                    </span>
                    <span className="font-medium">{displayResults.summary.errors}</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Performance</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Duration</span>
                    <span className="font-medium">{displayResults.summary.execution_time_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Data Scanned</span>
                    <span className="font-medium">
                      {(displayResults.summary.data_scanned_bytes / 1024).toFixed(1)}KB
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg per Test</span>
                    <span className="font-medium">
                      {Math.round(displayResults.summary.execution_time_ms / displayResults.summary.total_tests)}ms
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Status Chart */}
            {statusData.length > 0 && (
              <div className="h-32">
                <h4 className="font-medium text-sm mb-2">Test Distribution</h4>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={20}
                      outerRadius={50}
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="details" className="flex-1">
            <div className="space-y-2 max-h-64 overflow-auto">
              {displayResults.test_results.map((test: any) => (
                <div key={test.id} className="flex items-center justify-between p-3 border rounded-md">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(test.status)}
                    <div>
                      <p className="font-medium text-sm">{test.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {test.duration_ms}ms
                        {test.violations !== undefined && ` • ${test.violations} violations`}
                        {test.error && ` • ${test.error}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusBadge(test.status)}>
                      {test.status}
                    </Badge>
                    {(test.status === 'fail' || test.error) && (
                      <Button variant="ghost" size="sm">
                        <FileText className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="metrics" className="flex-1">
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-sm mb-2">Test Duration (ms)</h4>
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={durationData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" fontSize={10} />
                      <YAxis fontSize={10} />
                      <Tooltip />
                      <Bar dataKey="duration" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
