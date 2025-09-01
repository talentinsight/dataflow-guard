'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { RunsTable } from '@/components/runs-table'
import { StatsCards } from '@/components/stats-cards'
import { apiClient } from '@/lib/api-client'
import { PlayCircle, Plus, Settings, Database } from 'lucide-react'
import Link from 'next/link'

export default function HomePage() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: () => apiClient.listRuns({ limit: 10 }),
  })

  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Testing Orchestrator</h1>
          <p className="text-muted-foreground">
            Zero-SQL, AI-assisted data testing framework
          </p>
        </div>
        <div className="flex items-center gap-2">
          {healthData && (
            <Badge variant={healthData.status === 'healthy' ? 'default' : 'destructive'}>
              API {healthData.status}
            </Badge>
          )}
          <Button asChild>
            <Link href="/builder">
              <Plus className="mr-2 h-4 w-4" />
              New Test Suite
            </Link>
          </Button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="cursor-pointer transition-colors hover:bg-muted/50">
          <Link href="/builder">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Test Builder</CardTitle>
              <Plus className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Create tests with Zero-SQL cards
              </p>
            </CardContent>
          </Link>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-muted/50">
          <Link href="/runs">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Run History</CardTitle>
              <PlayCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                View test execution results
              </p>
            </CardContent>
          </Link>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-muted/50">
          <Link href="/datasets">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Datasets</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Browse catalog and schemas
              </p>
            </CardContent>
          </Link>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-muted/50">
          <Link href="/settings">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Settings</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Connections, policies, AI providers
              </p>
            </CardContent>
          </Link>
        </Card>
      </div>

      {/* Stats Overview */}
      <StatsCards />

      {/* Recent Runs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Test Runs</CardTitle>
              <CardDescription>
                Latest test executions across all suites
              </CardDescription>
            </div>
            <Button variant="outline" asChild>
              <Link href="/runs">View All</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <RunsTable data={runs?.runs || []} isLoading={isLoading} compact />
        </CardContent>
      </Card>
    </div>
  )
}
