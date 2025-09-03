'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useWorkspaceStore } from '@/stores/workspace'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/common/EmptyState'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Play, Square, RotateCcw, Activity, CheckCircle, XCircle, Clock } from 'lucide-react'

export function RunConsole() {
  const { 
    runId, 
    setRunId, 
    status, 
    setStatus, 
    getSelectedTestCount,
    selectedTests,
    builderText,
    datasetName,
    datasetMeta 
  } = useWorkspaceStore()

  const [logs, setLogs] = useState<string[]>([])

  // Poll run status when we have an active run
  const { data: runData } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runId ? apiClient.getRun(runId) : null,
    enabled: !!runId && status === 'running',
    refetchInterval: 2000, // Poll every 2 seconds
  })

  // Start run mutation
  const startRunMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/runs/demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_tests: Array.from(selectedTests),
          dataset: datasetName,
          dry_run: true
        })
      })
      return response.json()
    },
    onSuccess: (data) => {
      setRunId(data.run_id)
      setStatus(data.status === 'completed' ? 'done' : 'running')
      setLogs([
        'Demo run started...',
        `Run ID: ${data.run_id}`,
        `Dataset: ${data.dataset}`,
        `Tests: ${data.test_count} compiled`,
        data.message
      ])
    },
    onError: (error) => {
      setStatus('error')
      setLogs(prev => [...prev, `Error: ${error.message}`])
    }
  })

  // Update status based on run data
  useEffect(() => {
    if (runData) {
      const newStatus = runData.status
      if (newStatus !== status) {
        setStatus(newStatus)
        setLogs(prev => [...prev, `Status changed to: ${newStatus}`])
        
        if (newStatus === 'completed' || newStatus === 'failed') {
          setLogs(prev => [...prev, `Run ${newStatus} at ${new Date().toLocaleTimeString()}`])
        }
      }
    }
  }, [runData, status, setStatus])

  const handleStartRun = () => {
    const selectedCount = getSelectedTestCount()
    
    if (selectedCount === 0) {
      setLogs(['Error: No tests selected. Please select tests from the Plan panel.'])
      return
    }

    if (!datasetName || datasetName.trim() === '') {
      setLogs(['Error: No dataset specified. Please enter a dataset name.'])
      return
    }

    setLogs(['Preparing to start run...'])
    startRunMutation.mutate()
  }

  const handleStopRun = () => {
    setStatus('idle')
    setRunId(null)
    setLogs(prev => [...prev, 'Run stopped by user'])
  }

  const handleResetRun = () => {
    setStatus('idle')
    setRunId(null)
    setLogs([])
  }

  const canStart = status === 'idle' && getSelectedTestCount() > 0 && datasetName.trim() !== ''
  const canStop = status === 'running'
  const canReset = status !== 'idle'

  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
      case 'done':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'done':
        return 'bg-green-100 text-green-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <div>
              <CardTitle className="text-base">Run Console</CardTitle>
              <CardDescription className="text-sm">Execute tests and monitor progress</CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge className={getStatusColor()}>
              {status}
            </Badge>
            {runId && (
              <Badge variant="outline" className="text-xs font-mono">
                {runId.slice(-8)}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-4 space-y-4">
        {/* Control Buttons */}
        <div className="flex items-center space-x-2">
          <Button 
            onClick={handleStartRun}
            disabled={!canStart || startRunMutation.isPending}
            size="sm"
          >
            <Play className="mr-2 h-3 w-3" />
            {startRunMutation.isPending ? 'Starting...' : 'Run Tests'}
          </Button>
          
          {canStop && (
            <Button variant="outline" onClick={handleStopRun} size="sm">
              <Square className="mr-2 h-3 w-3" />
              Stop
            </Button>
          )}
          
          {canReset && (
            <Button variant="ghost" onClick={handleResetRun} size="sm">
              <RotateCcw className="mr-2 h-3 w-3" />
              Reset
            </Button>
          )}
        </div>

        {/* Run Summary */}
        {(getSelectedTestCount() > 0 || builderText || datasetMeta) && (
          <div className="p-3 bg-muted/30 rounded-md space-y-2">
            <h4 className="font-medium text-sm">Run Configuration</h4>
            <div className="space-y-1 text-xs text-muted-foreground">
              <div>Tests: {getSelectedTestCount()} selected</div>
              <div>Dataset: {datasetName || 'None specified'}</div>
              <div>Mode: Demo (auto-compile)</div>
            </div>
          </div>
        )}

        {/* Logs */}
        <div className="flex-1 flex flex-col">
          <h4 className="font-medium text-sm mb-2">Execution Log</h4>
          <div className="flex-1 border rounded-md bg-black/5 p-3 font-mono text-xs overflow-auto">
            {logs.length === 0 ? (
              <EmptyState
                title="No activity"
                description="Start a test run to see execution logs"
              />
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="text-muted-foreground">
                    <span className="text-muted-foreground/60">
                      [{new Date().toLocaleTimeString()}]
                    </span>{' '}
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Run Progress */}
        {status === 'running' && runData && (
          <div className="p-3 border rounded-md">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Progress</span>
              <span className="text-xs text-muted-foreground">
                {runData.completed_tests || 0} / {runData.total_tests || getSelectedTestCount()}
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${((runData.completed_tests || 0) / (runData.total_tests || getSelectedTestCount())) * 100}%` 
                }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
