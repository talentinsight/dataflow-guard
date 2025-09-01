'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Play, Search, Filter } from 'lucide-react'

export default function RunsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: runsData, isLoading } = useQuery({
    queryKey: ['runs', { status: statusFilter !== 'all' ? statusFilter : undefined }],
    queryFn: () => apiClient.getRuns({ 
      status: statusFilter !== 'all' ? statusFilter : undefined 
    }),
  })

  const getStatusBadge = (status: string) => {
    const variants = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
    }
    return variants[status as keyof typeof variants] || 'bg-gray-100 text-gray-800'
  }

  const mockRuns = [
    { id: '1', suite_name: 'Customer Data Validation', status: 'success', started_at: '2025-01-09T10:00:00Z', duration_ms: 45000 },
    { id: '2', suite_name: 'Order Processing Check', status: 'success', started_at: '2025-01-09T09:30:00Z', duration_ms: 72000 },
    { id: '3', suite_name: 'Payment Gateway Tests', status: 'failed', started_at: '2025-01-09T09:00:00Z', duration_ms: 32000 },
    { id: '4', suite_name: 'Inventory Sync Validation', status: 'running', started_at: '2025-01-09T08:45:00Z', duration_ms: null },
    { id: '5', suite_name: 'User Authentication Flow', status: 'success', started_at: '2025-01-09T08:00:00Z', duration_ms: 125000 },
  ]

  const runs = runsData?.runs || mockRuns
  const filteredRuns = runs.filter((run: any) => 
    run.suite_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between space-y-2 mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Test Runs</h1>
          <p className="text-muted-foreground">Monitor and manage your test executions</p>
        </div>
        <Button>
          <Play className="mr-2 h-4 w-4" />
          Run All Tests
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search test suites..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Runs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
          <CardDescription>
            {filteredRuns.length} run{filteredRuns.length !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRuns.map((run: any) => (
                <div key={run.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className={`h-3 w-3 rounded-full ${
                      run.status === 'success' ? 'bg-green-500' :
                      run.status === 'failed' ? 'bg-red-500' :
                      run.status === 'running' ? 'bg-blue-500 animate-pulse' :
                      'bg-yellow-500'
                    }`} />
                    <div>
                      <p className="font-medium">{run.suite_name}</p>
                      <p className="text-sm text-muted-foreground">
                        Started: {new Date(run.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <Badge className={getStatusBadge(run.status)}>
                        {run.status}
                      </Badge>
                      {run.duration_ms && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {Math.round(run.duration_ms / 1000)}s
                        </p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                      <Button variant="ghost" size="sm">
                        Re-run
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {filteredRuns.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No runs found matching your criteria.
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
