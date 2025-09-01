'use client'

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Upload, Database, FileText, Eye, Download } from 'lucide-react'

interface DatasetPreview {
  name: string
  rows: any[]
  columns: { name: string; type: string }[]
  totalRows: number
}

export default function DatasetsPage() {
  const [activeTab, setActiveTab] = useState('catalog')
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [previewData, setPreviewData] = useState<DatasetPreview | null>(null)

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => apiClient.getDatasets(),
  })

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setUploadedFiles(prev => [...prev, ...files])
    
    // Preview first file if it's CSV/JSON
    if (files.length > 0) {
      const file = files[0]
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        previewCSV(file)
      } else if (file.type === 'application/json' || file.name.endsWith('.json')) {
        previewJSON(file)
      }
    }
  }, [])

  const previewCSV = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const lines = text.split('\n').filter(line => line.trim())
      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
      const rows = lines.slice(1, 201).map(line => {
        const values = line.split(',').map(v => v.trim().replace(/"/g, ''))
        return headers.reduce((obj, header, index) => {
          obj[header] = values[index] || ''
          return obj
        }, {} as any)
      })

      setPreviewData({
        name: file.name,
        columns: headers.map(name => ({ name, type: 'string' })), // Simple type inference could be added
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
        const rows = Array.isArray(jsonData) ? jsonData.slice(0, 200) : [jsonData]
        const columns = rows.length > 0 ? 
          Object.keys(rows[0]).map(name => ({ name, type: typeof rows[0][name] })) : []

        setPreviewData({
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

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
    if (index === 0 && uploadedFiles.length === 1) {
      setPreviewData(null)
    }
  }

  const mockDatasets = [
    { name: 'ORDERS', schema: 'RAW', tables: 1, last_updated: '2025-01-09T10:00:00Z', row_count: 125000 },
    { name: 'CUSTOMERS', schema: 'RAW', tables: 1, last_updated: '2025-01-09T09:30:00Z', row_count: 50000 },
    { name: 'PRODUCTS', schema: 'PREP', tables: 1, last_updated: '2025-01-09T09:00:00Z', row_count: 15000 },
    { name: 'ORDERS_SUMMARY', schema: 'MART', tables: 1, last_updated: '2025-01-09T08:30:00Z', row_count: 12000 },
  ]

  const catalogDatasets = datasets?.datasets || mockDatasets

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between space-y-2 mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
          <p className="text-muted-foreground">Manage and explore your data sources</p>
        </div>
        <Button>
          <Database className="mr-2 h-4 w-4" />
          Connect Data Source
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="catalog">Data Catalog</TabsTrigger>
          <TabsTrigger value="upload">Upload Data</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog" className="space-y-4">
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
                        <Button variant="outline" size="sm">
                          <Eye className="mr-2 h-4 w-4" />
                          View Schema
                        </Button>
                        <Button variant="ghost" size="sm">
                          <FileText className="mr-2 h-4 w-4" />
                          Stats
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload Dataset</CardTitle>
              <CardDescription>
                Upload CSV, JSON, or Parquet files for testing (max 100MB per file)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* File Upload Area */}
                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <div className="space-y-2">
                    <p className="text-lg font-medium">Drop files here or click to browse</p>
                    <p className="text-sm text-muted-foreground">
                      Supports CSV, JSON, JSONL, and Parquet files
                    </p>
                  </div>
                  <input
                    type="file"
                    multiple
                    accept=".csv,.json,.jsonl,.parquet"
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                </div>

                {/* Uploaded Files List */}
                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium">Uploaded Files</h4>
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <FileText className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium">{file.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button variant="outline" size="sm" onClick={() => setActiveTab('preview')}>
                            Preview
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => removeFile(index)}>
                            Remove
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preview" className="space-y-4">
          {previewData ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{previewData.name}</CardTitle>
                    <CardDescription>
                      Showing first 200 rows of {previewData.totalRows.toLocaleString()} total rows
                    </CardDescription>
                  </div>
                  <Button variant="outline">
                    <Download className="mr-2 h-4 w-4" />
                    Export Sample
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {/* Column Info */}
                <div className="mb-4">
                  <h4 className="font-medium mb-2">Columns ({previewData.columns.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {previewData.columns.map((col, index) => (
                      <Badge key={index} variant="outline">
                        {col.name} ({col.type})
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Data Table */}
                <div className="border rounded-lg overflow-auto max-h-96">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr>
                        {previewData.columns.map((col, index) => (
                          <th key={index} className="px-4 py-2 text-left font-medium">
                            {col.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.rows.map((row, rowIndex) => (
                        <tr key={rowIndex} className="border-t">
                          {previewData.columns.map((col, colIndex) => (
                            <td key={colIndex} className="px-4 py-2 max-w-xs truncate">
                              {String(row[col.name] || '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <p className="text-lg font-medium">No data to preview</p>
                  <p className="text-sm text-muted-foreground">
                    Upload a file to see a preview of your data
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
