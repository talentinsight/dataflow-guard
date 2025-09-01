'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'
import { TrendingUp, TrendingDown, Activity, Clock } from 'lucide-react'

export function StatsCards() {
  const { data: runs } = useQuery({
    queryKey: ['runs', 'stats'],
    queryFn: () => apiClient.listRuns({ limit: 100 }),
  })

  // Calculate stats from recent runs
  const stats = runs?.runs ? {
    totalRuns: runs.runs.length,
    successRate: runs.runs.length > 0 
      ? Math.round((runs.runs.filter(r => r.status === 'completed').length / runs.runs.length) * 100)
      : 0,
    avgDuration: runs.runs.length > 0
      ? Math.round(runs.runs
          .filter(r => r.execution_time_ms)
          .reduce((acc, r) => acc + (r.execution_time_ms || 0), 0) / 
          runs.runs.filter(r => r.execution_time_ms).length / 1000)
      : 0,
    activeRuns: runs.runs.filter(r => r.status === 'running').length,
  } : {
    totalRuns: 0,
    successRate: 0,
    avgDuration: 0,
    activeRuns: 0,
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalRuns}</div>
          <p className="text-xs text-muted-foreground">
            Last 100 executions
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.successRate}%</div>
          <p className="text-xs text-muted-foreground">
            Completed successfully
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.avgDuration}s</div>
          <p className="text-xs text-muted-foreground">
            Per test suite
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Runs</CardTitle>
          <TrendingDown className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.activeRuns}</div>
          <p className="text-xs text-muted-foreground">
            Currently running
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
