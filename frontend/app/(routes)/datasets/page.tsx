'use client'

// LEGACY: Dataset management is now integrated into the Workbench
// This page provides basic dataset browsing with a link to the workbench

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { apiClient } from '@/lib/apiClient'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Database, ArrowRight } from 'lucide-react'

export default function DatasetsPage() {
  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => apiClient.getDatasets(),
    retry: false,
  })

  const mockDatasets = [
    { name: 'ORDERS', schema: 'RAW', row_count: 125000, last_updated: '2025-01-09T10:00:00Z' },
    { name: 'CUSTOMERS', schema: 'RAW', row_count: 50000, last_updated: '2025-01-09T09:30:00Z' },
    { name: 'PRODUCTS', schema: 'PREP', row_count: 15000, last_updated: '2025-01-09T09:00:00Z' },
    { name: 'ORDERS_SUMMARY', schema: 'MART', row_count: 12000, last_updated: '2025-01-09T08:30:00Z' },
  ]

  const catalogDatasets = datasets?.datasets || mockDatasets

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between space-y-2 mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
          <p className="text-muted-foreground">Browse available datasets</p>
        </div>
        <Button asChild>
          <Link href="/workbench">
            <ArrowRight className="mr-2 h-4 w-4" />
            Go to Workbench
          </Link>
        </Button>
      </div>

      <Card className="mb-4 bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3">
            <div className="h-2 w-2 rounded-full bg-blue-500"></div>
            <p className="text-sm">
              <strong>New:</strong> Dataset management has moved to the{' '}
              <Link href="/workbench" className="text-blue-600 hover:underline">
                Workbench
              </Link>
              {' '}for a unified testing experience.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Available Datasets</CardTitle>
          <CardDescription>
            {catalogDatasets.length} dataset{catalogDatasets.length !== 1 ? 's' : ''} in catalog
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {catalogDatasets.map((dataset: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <Database className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <h3 className="font-medium">{dataset.schema}.{dataset.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {dataset.row_count?.toLocaleString() || 'Unknown'} rows • 
                        Last updated: {new Date(dataset.last_updated).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">{dataset.schema}</Badge>
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/workbench">
                        Use in Workbench
                      </Link>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}