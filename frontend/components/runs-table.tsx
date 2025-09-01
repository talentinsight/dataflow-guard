'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatDate, formatDuration, getRunStatusColor } from '@/lib/utils'
import { RunSummary } from '@/lib/api-client'
import { ExternalLink, Play } from 'lucide-react'
import Link from 'next/link'

interface RunsTableProps {
  data: RunSummary[]
  isLoading?: boolean
  compact?: boolean
}

export function RunsTable({ data, isLoading, compact = false }: RunsTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 bg-muted animate-pulse rounded" />
        ))}
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No test runs found
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {data.map((run) => (
        <div
          key={run.run_id}
          className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium truncate">{run.suite_name}</h4>
                  <Badge
                    variant={run.status === 'completed' ? 'default' : 
                            run.status === 'failed' ? 'destructive' : 'secondary'}
                  >
                    {run.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                  <span>{formatDate(run.started_at)}</span>
                  {run.execution_time_ms && (
                    <span>{formatDuration(run.execution_time_ms)}</span>
                  )}
                  <span>{run.environment}</span>
                </div>
              </div>
              
              {!compact && (
                <div className="flex items-center gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-medium text-green-600">{run.passed_tests}</div>
                    <div className="text-muted-foreground">Passed</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-red-600">{run.failed_tests}</div>
                    <div className="text-muted-foreground">Failed</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-orange-600">{run.error_tests}</div>
                    <div className="text-muted-foreground">Errors</div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/runs/${run.run_id}`}>
                <ExternalLink className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
