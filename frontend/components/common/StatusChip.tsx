'use client'

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'

export function StatusChip() {
  const { data: healthData, isError } = useQuery({
    queryKey: ['health'],
    queryFn: apiClient.getHealth,
    refetchInterval: 10000, // Poll every 10 seconds
    retry: false,
  })

  const isHealthy = healthData && !isError
  
  return (
    <div className="flex items-center space-x-2 text-sm">
      <div className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-muted-foreground">
        {isHealthy ? 'System Healthy' : 'System Offline'}
      </span>
    </div>
  )
}
