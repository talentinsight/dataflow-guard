'use client'

import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useWorkspaceStore } from '@/stores/workspace'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/common/EmptyState'
import { Upload, Database, FileText, Eye, X } from 'lucide-react'

export function DatasetPanel() {
  const { datasetMeta, setDatasetMeta } = useWorkspaceStore()

  // Query for available datasets (graceful fallback)
  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => apiClient.getDatasets(),
    retry: false,
  })

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    if (files.length === 0) return

    const file = files[0]
    
    // Preview first file if it's CSV/JSON
    if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
      previewCSV(file)
    } else if (file.type === 'application/json' || file.name.endsWith('.json')) {
      previewJSON(file)
    }
  }, [])

  const previewCSV = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const lines = text.split('\n').filter(line => line.trim())
      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
      const rows = lines.slice(1, 101).map(line => {
        const values = line.split(',').map(v => v.trim().replace(/"/g, ''))
        return headers.reduce((obj, header, index) => {
          obj[header] = values[index] || ''
          return obj
        }, {} as any)
      })

      setDatasetMeta({
        name: file.name,
        columns: headers.map(name => ({ name, type: 'string' })),
        rows,
        totalRows: lines.length - 1
      })
    }
    reader.readAsText(file)
  }

  const previewJSON = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const jsonData = JSON.parse(e.target?.result as string)
        const rows = Array.isArray(jsonData) ? jsonData.slice(0, 100) : [jsonData]
        const columns = rows.length > 0 ? 
          Object.keys(rows[0]).map(name => ({ name, type: typeof rows[0][name] })) : []

        setDatasetMeta({
          name: file.name,
          columns,
          rows,
          totalRows: Array.isArray(jsonData) ? jsonData.length : 1
        })
      } catch (error) {
        console.error('Error parsing JSON:', error)
      }
    }
    reader.readAsText(file)
  }

  const clearDataset = () => {
    setDatasetMeta(null)
  }

  // Mock datasets for fallback
  const mockDatasets = [
    { name: 'ORDERS', schema: 'RAW', row_count: 125000, last_updated: '2025-01-09T10:00:00Z' },
    { name: 'CUSTOMERS', schema: 'RAW', row_count: 50000, last_updated: '2025-01-09T09:30:00Z' },
    { name: 'PRODUCTS', schema: 'PREP', row_count: 15000, last_updated: '2025-01-09T09:00:00Z' },
  ]

  const availableDatasets = datasets?.datasets || mockDatasets

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <div>
              <CardTitle className="text-base">Dataset</CardTitle>
              <CardDescription className="text-sm">Upload or select data for testing</CardDescription>
            </div>
          </div>
          {datasetMeta && (
            <Button variant="ghost" size="sm" onClick={clearDataset}>
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-4 space-y-4">
        {datasetMeta ? (
          // Dataset Preview
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">{datasetMeta.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {datasetMeta.totalRows.toLocaleString()} rows • {datasetMeta.columns.length} columns
                </p>
              </div>
              <Badge variant="outline">Preview</Badge>
            </div>

            {/* Column Info */}
            <div>
              <h4 className="font-medium text-sm mb-2">Columns</h4>
              <div className="flex flex-wrap gap-1">
                {datasetMeta.columns.slice(0, 6).map((col, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {col.name}
                  </Badge>
                ))}
                {datasetMeta.columns.length > 6 && (
                  <Badge variant="outline" className="text-xs">
                    +{datasetMeta.columns.length - 6} more
                  </Badge>
                )}
              </div>
            </div>

            {/* Data Preview Table */}
            <div className="flex-1 border rounded-md overflow-hidden">
              <div className="max-h-48 overflow-auto">
                <table className="w-full text-xs">
                  <thead className="bg-muted/50 sticky top-0">
                    <tr>
                      {datasetMeta.columns.slice(0, 4).map((col, index) => (
                        <th key={index} className="px-2 py-1 text-left font-medium border-r">
                          {col.name}
                        </th>
                      ))}
                      {datasetMeta.columns.length > 4 && (
                        <th className="px-2 py-1 text-left font-medium">...</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {datasetMeta.rows.slice(0, 10).map((row, rowIndex) => (
                      <tr key={rowIndex} className="border-t">
                        {datasetMeta.columns.slice(0, 4).map((col, colIndex) => (
                          <td key={colIndex} className="px-2 py-1 border-r max-w-20 truncate">
                            {String(row[col.name] || '')}
                          </td>
                        ))}
                        {datasetMeta.columns.length > 4 && (
                          <td className="px-2 py-1">...</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          // Upload or Select Dataset
          <div className="space-y-4">
            {/* File Upload */}
            <div className="relative border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center hover:border-muted-foreground/50 transition-colors">
              <Upload className="mx-auto h-8 w-8 text-muted-foreground/50 mb-3" />
              <div className="space-y-1">
                <p className="font-medium">Upload dataset</p>
                <p className="text-sm text-muted-foreground">
                  CSV, JSON, or JSONL files
                </p>
              </div>
              <input
                type="file"
                accept=".csv,.json,.jsonl"
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>

            {/* Available Datasets */}
            <div>
              <h4 className="font-medium text-sm mb-2">Available Datasets</h4>
              {isLoading ? (
                <div className="flex items-center justify-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : availableDatasets.length === 0 ? (
                <EmptyState
                  icon={<Database className="h-8 w-8" />}
                  title="No datasets"
                  description="Upload a file or connect a data source"
                />
              ) : (
                <div className="space-y-2 max-h-32 overflow-auto">
                  {availableDatasets.map((dataset: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded-md hover:bg-muted/50 transition-colors">
                      <div className="flex items-center space-x-2">
                        <Database className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="font-medium text-sm">{dataset.schema}.{dataset.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {dataset.row_count?.toLocaleString() || 'Unknown'} rows
                          </p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
