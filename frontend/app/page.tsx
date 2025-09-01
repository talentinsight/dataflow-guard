'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Activity, Database, TestTube, TrendingUp } from 'lucide-react'

export default function DashboardPage() {
  // Fetch dashboard data
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: apiClient.getHealth,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const { data: runsData } = useQuery({
    queryKey: ['runs', { limit: 5 }],
    queryFn: () => apiClient.getRuns(),
  })

  const mockStats = {
    totalTests: 2847,
    successRate: 96.8,
    avgDuration: '1.4m',
    activeRuns: 7
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <Link href="/" className="mr-6 flex items-center space-x-2">
              <TestTube className="h-6 w-6" />
              <span className="font-bold">DataFlowGuard</span>
            </Link>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <Link href="/" className="text-foreground/60 transition-colors hover:text-foreground/80">
                Dashboard
              </Link>
              <Link href="/runs" className="text-foreground/60 transition-colors hover:text-foreground/80">
                Runs
              </Link>
              <Link href="/builder" className="text-foreground/60 transition-colors hover:text-foreground/80">
                Test Builder
              </Link>
              <Link href="/datasets" className="text-foreground/60 transition-colors hover:text-foreground/80">
                Datasets
              </Link>
              <Link href="/settings" className="text-foreground/60 transition-colors hover:text-foreground/80">
                Settings
              </Link>
            </nav>
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className={`h-2 w-2 rounded-full ${healthData ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-muted-foreground">
                {healthData ? 'System Healthy' : 'System Offline'}
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-between space-y-2 mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <div className="flex items-center space-x-2">
            <Button asChild>
              <Link href="/builder">
                <TestTube className="mr-2 h-4 w-4" />
                New Test Suite
              </Link>
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tests</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{mockStats.totalTests.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">+12% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{mockStats.successRate}%</div>
              <p className="text-xs text-muted-foreground">+2.1% improvement</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{mockStats.avgDuration}</div>
              <p className="text-xs text-muted-foreground">15% faster</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Runs</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{mockStats.activeRuns}</div>
              <p className="text-xs text-muted-foreground">Currently running</p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Runs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Test Runs</CardTitle>
                <CardDescription>Latest executions and their status</CardDescription>
              </div>
              <Button variant="outline" asChild>
                <Link href="/runs">View All</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {runsData?.runs?.slice(0, 5).map((run: any) => (
                <div key={run.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className={`h-3 w-3 rounded-full ${
                      run.status === 'success' ? 'bg-green-500' :
                      run.status === 'failed' ? 'bg-red-500' :
                      'bg-blue-500'
                    }`} />
                    <div>
                      <p className="font-medium">{run.suite_name || 'Test Suite'}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(run.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      run.status === 'success' 
                        ? 'bg-green-100 text-green-800' 
                        : run.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {run.status}
                    </span>
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/runs/${run.id}`}>View</Link>
                    </Button>
                  </div>
                </div>
              )) || (
                // Mock data when API is not available
                <>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="h-3 w-3 rounded-full bg-green-500" />
                      <div>
                        <p className="font-medium">Customer Data Validation</p>
                        <p className="text-sm text-muted-foreground">2 minutes ago</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        success
                      </span>
                      <Button variant="ghost" size="sm">View</Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="h-3 w-3 rounded-full bg-red-500" />
                      <div>
                        <p className="font-medium">Payment Gateway Tests</p>
                        <p className="text-sm text-muted-foreground">15 minutes ago</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        failed
                      </span>
                      <Button variant="ghost" size="sm">View</Button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}