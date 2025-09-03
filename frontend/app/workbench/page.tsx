'use client'

import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { StatusChip } from '@/components/common/StatusChip'
import {
  Upload,
  Play,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Zap,
  GitBranch,
  Clock,
  Folder,
  Target,
  FolderOpen,
  Table
} from 'lucide-react'

const queryClient = new QueryClient()

export default function WorkbenchPage() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [testResults, setTestResults] = useState<any[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState('validation')
  const [useHybridTests, setUseHybridTests] = useState(true)
  const [aiTestsEnabled, setAiTestsEnabled] = useState(true)
  const [customAiTests, setCustomAiTests] = useState<string[]>([])
  const [databases, setDatabases] = useState<any[]>([])
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [loadingNodes, setLoadingNodes] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadDatabases()
  }, [])

  const loadDatabases = async () => {
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/api/v1/metadata/databases`, {
        headers: { 'Cache-Control': 'max-age=300' }
      })
      const data = await response.json()
      setDatabases(data.databases || [])
    } catch (error) {
      console.error('Failed to load databases:', error)
      setDatabases([])
    }
  }

  const loadSchemas = async (databaseName: string) => {
    const nodeKey = `db:${databaseName}`
    setLoadingNodes(prev => new Set([...Array.from(prev), nodeKey]))
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/api/v1/metadata/schemas/${databaseName}`)
      const data = await response.json()
      setDatabases(prev =>
        prev.map(db =>
          db.DATABASE_NAME === databaseName ? { ...db, schemas: data.schemas || [] } : db
        )
      )
    } catch (error) {
      console.error('Failed to load schemas:', error)
    } finally {
      setLoadingNodes(prev => {
        const next = new Set(prev)
        next.delete(nodeKey)
        return next
      })
    }
  }

  const loadTables = async (databaseName: string, schemaName: string) => {
    const nodeKey = `schema:${databaseName}.${schemaName}`
    setLoadingNodes(prev => new Set([...Array.from(prev), nodeKey]))
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/api/v1/metadata/tables/${databaseName}/${schemaName}`)
      const data = await response.json()
      setDatabases(prev =>
        prev.map(db =>
          db.DATABASE_NAME === databaseName
            ? {
                ...db,
                schemas: db.schemas?.map((schema: any) =>
                  schema.SCHEMA_NAME === schemaName ? { ...schema, tables: data.tables || [] } : schema
                )
              }
            : db
        )
      )
    } catch (error) {
      console.error('Failed to load tables:', error)
    } finally {
      setLoadingNodes(prev => {
        const next = new Set(prev)
        next.delete(nodeKey)
        return next
      })
    }
  }

  const toggleNode = (nodeKey: string, databaseName?: string, schemaName?: string) => {
    if (expandedNodes.has(nodeKey)) {
      setExpandedNodes(prev => {
        const next = new Set(prev)
        next.delete(nodeKey)
        return next
      })
    } else {
      setExpandedNodes(prev => new Set([...Array.from(prev), nodeKey]))
      if (nodeKey.startsWith('db:') && databaseName) {
        const db = databases.find(d => d.DATABASE_NAME === databaseName)
        if (!db?.schemas) loadSchemas(databaseName)
      } else if (nodeKey.startsWith('schema:') && databaseName && schemaName) {
        const db = databases.find(d => d.DATABASE_NAME === databaseName)
        const schema = db?.schemas?.find((s: any) => s.SCHEMA_NAME === schemaName)
        if (!schema?.tables) loadTables(databaseName, schemaName)
      }
    }
  }

  const selectTable = (databaseName: string, schemaName: string, tableName: string) => {
    const fullTableName = `${databaseName}.${schemaName}.${tableName}`
    if (schemaName.toUpperCase().includes('RAW')) {
      const el = document.querySelector('input[placeholder="Select from browser above"]') as HTMLInputElement | null
      if (el) el.value = fullTableName
    } else if (schemaName.toUpperCase().includes('PREP')) {
      const el = document.querySelector('input[placeholder="Select prep table from browser"]') as HTMLInputElement | null
      if (el) el.value = fullTableName
    } else if (schemaName.toUpperCase().includes('MART')) {
      const el = document.querySelector('input[placeholder="Select mart table from browser"]') as HTMLInputElement | null
      if (el) el.value = fullTableName
    } else {
      const el = document.querySelector('input[placeholder="Select from browser above"]') as HTMLInputElement | null
      if (el) el.value = fullTableName
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) setUploadedFile(file)
  }

  const handleRunPipeline = async () => {
    setIsRunning(true)
    setTestResults([])
    try {
      const sourceInput = document.querySelector('input[placeholder="Select from browser above"]') as HTMLInputElement | null
      const prepInput = document.querySelector('input[placeholder="Select prep table from browser"]') as HTMLInputElement | null
      const martInput = document.querySelector('input[placeholder="Select mart table from browser"]') as HTMLInputElement | null
      const sourceTable = sourceInput?.value || ''
      const prepTable = prepInput?.value || ''
      const martTable = martInput?.value || ''
      if (!sourceTable.trim()) {
        setTestResults([{ status: 'error', message: 'Please select a source table from the database browser.' }])
        setIsRunning(false)
        return
      }
      if (!prepTable.trim()) {
        setTestResults([{ status: 'error', message: 'Please select a prep table from the database browser.' }])
        setIsRunning(false)
        return
      }
      if (!martTable.trim()) {
        setTestResults([{ status: 'error', message: 'Please select a mart table from the database browser.' }])
        setIsRunning(false)
        return
      }
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const endpoint = useHybridTests ? '/api/v1/hybrid/test' : '/api/v1/pipeline/test/v2'
      const requestBody = useHybridTests
        ? {
            source_table: sourceTable,
            prep_table: prepTable,
            mart_table: martTable,
            test_types: ['row_count', 'null_check', 'email_format', 'transformation_accuracy'],
            natural_language_tests: aiTestsEnabled ? customAiTests.filter(t => t.trim()) : [],
            use_ai_fallback: aiTestsEnabled
          }
        : {
            source_table: sourceTable,
            prep_table: prepTable,
            mart_table: martTable,
            test_types: ['row_count', 'data_quality', 'transformation_validation', 'business_rules']
          }
      const response = await fetch(`${apiBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      const result = await response.json()
      if (useHybridTests && result.test_summary) {
        const hybridResults = [
          {
            name: '📊 Hybrid Test Summary',
            status: 'info',
            duration: `${result.test_summary.execution_time_seconds?.toFixed(1)}s`,
            details: {
              total_tests: result.test_summary.total_tests,
              static_tests: result.test_summary.static_tests,
              ai_tests: result.test_summary.ai_tests,
              passed: result.test_summary.passed,
              failed: result.test_summary.failed,
              ai_cost: result.cost_info?.estimated_ai_cost_usd || 0,
              ai_tokens: result.cost_info?.ai_cost_tokens || 0
            }
          },
          ...(result.static_results?.map((t: any) => ({
            name: `⚡ ${t.test_name}`,
            status: t.status === 'pass' ? 'passed' : t.status === 'fail' ? 'failed' : 'warning',
            duration: 'Static',
            details: t.raw_results,
            source: 'static'
          })) || []),
          ...(result.ai_results?.map((t: any) => ({
            name: `🤖 ${t.test_name}`,
            status: t.status === 'pass' ? 'passed' : t.status === 'fail' ? 'failed' : 'warning',
            duration: `${t.tokens || 0} tokens`,
            details: { sql: t.generated_sql, explanation: t.explanation, tokens: t.tokens, provider: t.provider },
            source: 'ai'
          })) || [])
        ]
        setTestResults(hybridResults)
        setIsRunning(false)
        return
      }
      const runId = result.run_id
      const pollStatus = async () => {
        try {
          const statusRes = await fetch(`${apiBaseUrl}/api/v1/pipeline/test/v2/${runId}`)
          const status = await statusRes.json()
          if (status.status === 'completed' && status.comprehensive_results) {
            const comprehensiveResults = [
              {
                name: '📊 Test Summary',
                status: 'info',
                duration: `${status.test_summary?.execution_time_seconds?.toFixed(1)}s`,
                details: {
                  quality_score: status.data_quality_score,
                  total_tests: status.test_summary?.total_tests,
                  passed: status.test_summary?.passed,
                  failed: status.test_summary?.failed,
                  html_report_url: status.html_report_url
                }
              },
              ...status.comprehensive_results.test_results.map((t: any) => ({
                name: t.test_name,
                status: t.status === 'pass' ? 'passed' : t.status === 'fail' ? 'failed' : 'warning',
                duration: 'Completed',
                details: t.metrics,
                issues: t.issues
              }))
            ]
            setTestResults(comprehensiveResults)
          } else {
            setTestResults([{ name: status.current_step || 'Initializing', status: 'running', duration: 'Running...' }])
          }
          if (status.status === 'completed' || status.status === 'failed') {
            setIsRunning(false)
            return
          }
          setTimeout(pollStatus, 2000)
        } catch (e) {
          console.error('Polling error:', e)
          setIsRunning(false)
        }
      }
      setTimeout(pollStatus, 1000)
    } catch (error) {
      console.error('Pipeline start error:', error)
      setIsRunning(false)
      setTestResults([{ name: 'Pipeline Start', status: 'failed', duration: '0s' }])
    }
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        {/* Modern Header */}
        <header className="bg-white/80 backdrop-blur-lg border-b border-slate-200/60 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg">
                    <Zap className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                      DataFlowGuard
                    </h1>
                    <p className="text-xs text-slate-500 font-medium">ETL Pipeline Testing</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <StatusChip />
                <div className="flex items-center space-x-2 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-xs font-medium text-emerald-700">Snowflake Connected</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content - Compact Grid Layout */}
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-12 gap-6 p-6 min-h-0">
          {/* Left Panel - Pipeline Setup */}
          <div className="col-span-3 min-h-0">
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm h-full flex flex-col">
              <div className="p-3 border-b bg-gray-50/40 rounded-t-2xl">
                <div className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-gray-500" />
                  <span className="text-[13px] font-medium text-gray-600">Pipeline Setup</span>
                </div>
              </div>
              <div className="p-4 space-y-4 flex-1 overflow-auto">
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm text-gray-800">Database Browser</h4>
                  <div className="border rounded-lg p-3 bg-gray-50 min-h-[300px] max-h-[400px] overflow-y-auto text-sm">
                    <div className="space-y-1 text-xs">
                      {databases.map(database => {
                        const dbKey = `db:${database.DATABASE_NAME}`
                        const isDbExpanded = expandedNodes.has(dbKey)
                        const isDbLoading = loadingNodes.has(dbKey)
                        return (
                          <div key={database.DATABASE_NAME}>
                            <div
                              className="flex items-center space-x-1 hover:bg-gray-100 p-1 rounded cursor-pointer"
                              onClick={() => toggleNode(dbKey, database.DATABASE_NAME)}
                            >
                              {isDbLoading ? (
                                <Clock className="h-3 w-3 animate-spin" />
                              ) : isDbExpanded ? (
                                <FolderOpen className="h-3 w-3" />
                              ) : (
                                <Folder className="h-3 w-3" />
                              )}
                              <span className="font-medium text-gray-800">{database.DATABASE_NAME}</span>
                            </div>
                            {isDbExpanded && database.schemas && (
                              <div className="ml-4 space-y-1">
                                {database.schemas.map((schema: any) => {
                                  const schemaKey = `schema:${database.DATABASE_NAME}.${schema.SCHEMA_NAME}`
                                  const isSchemaExpanded = expandedNodes.has(schemaKey)
                                  const isSchemaLoading = loadingNodes.has(schemaKey)
                                  return (
                                    <div key={schema.SCHEMA_NAME}>
                                      <div
                                        className="flex items-center space-x-1 hover:bg-gray-100 p-1 rounded cursor-pointer"
                                        onClick={() => toggleNode(schemaKey, database.DATABASE_NAME, schema.SCHEMA_NAME)}
                                      >
                                        {isSchemaLoading ? (
                                          <Clock className="h-3 w-3 animate-spin" />
                                        ) : isSchemaExpanded ? (
                                          <FolderOpen className="h-3 w-3" />
                                        ) : (
                                          <Folder className="h-3 w-3" />
                                        )}
                                        <span className="text-gray-600">{schema.SCHEMA_NAME}</span>
                                      </div>
                                      {isSchemaExpanded && schema.tables && (
                                        <div className="ml-4 space-y-1">
                                          {schema.tables.map((table: any) => (
                                            <div
                                              key={table.TABLE_NAME}
                                              className="flex items-center space-x-1 text-blue-600 hover:bg-blue-50 p-1 rounded cursor-pointer"
                                              onClick={() => selectTable(database.DATABASE_NAME, schema.SCHEMA_NAME, table.TABLE_NAME)}
                                            >
                                              <Table className="h-3 w-3" />
                                              <span>
                                                {table.TABLE_NAME} ({table.ROW_COUNT || 0} rows)
                                              </span>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        )
                      })}
                      {databases.length === 0 && (
                        <div className="text-gray-500 text-center py-4">
                          <div className="animate-pulse">
                            <div className="h-3 bg-gray-200 rounded mb-2"></div>
                            <div className="h-3 bg-gray-200 rounded w-3/4 mx-auto"></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div>
                      <label className="text-xs font-medium text-gray-600 mb-1 block">Source Table</label>
                      <Input placeholder="Select from browser above" className="text-xs h-8" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-600 mb-1 block">Prep Table</label>
                      <Input placeholder="Select prep table from browser" className="text-xs h-8" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-600 mb-1 block">Mart Table</label>
                      <Input placeholder="Select mart table from browser" className="text-xs h-8" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center Panel - Test Configuration */}
          <div className="col-span-6 min-h-0">
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm h-full flex flex-col">
              <div className="p-4 flex-1 overflow-auto">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full h-full flex flex-col">
                  <TabsList className="h-8 text-xs rounded-md bg-gray-100 p-1 mb-4">
                    <TabsTrigger value="validation" className="px-2 py-1 data-[state=active]:bg-white data-[state=active]:shadow-sm">
                      Test Rules
                    </TabsTrigger>
                    <TabsTrigger value="upload" className="px-2 py-1 data-[state=active]:bg-white data-[state=active]:shadow-sm">
                      Data Upload
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="validation" className="space-y-6">
                    <div className="space-y-6">
                      <div>
                        <span className="text-[13px] font-medium text-gray-600 mb-3 block">Choose Test Engine</span>
                        <div className="flex gap-2">
                          <label className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs hover:bg-gray-100 cursor-pointer transition-colors ${useHybridTests ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300'}`}>
                            <input type="radio" name="testEngine" checked={useHybridTests} onChange={() => setUseHybridTests(true)} className="sr-only" />
                            <Zap className="h-4 w-4" />
                            Hybrid Engine
                          </label>
                          <label className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs hover:bg-gray-100 cursor-pointer transition-colors ${!useHybridTests ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300'}`}>
                            <input type="radio" name="testEngine" checked={!useHybridTests} onChange={() => setUseHybridTests(false)} className="sr-only" />
                            <Target className="h-4 w-4" />
                            Legacy Engine
                          </label>
                        </div>
                      </div>

                      <Separator />

                      <div>
                        <span className="text-[13px] font-medium text-gray-600 mb-3 block">Static Tests</span>
                        <div className="grid grid-cols-3 gap-2">
                          {[
                            { name: 'Row Count' },
                            { name: 'NULL Detection' },
                            { name: 'Email Format' },
                            { name: 'Transformation' },
                            { name: 'Duplicates' },
                            { name: 'Schema' }
                          ].map(t => (
                            <label key={t.name} className="flex items-center gap-2 rounded-md bg-gray-100/30 px-2 py-1.5 text-xs hover:bg-gray-100 cursor-pointer transition-colors">
                              <input type="checkbox" className="rounded text-blue-600" defaultChecked />
                              <span className="font-medium">{t.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {useHybridTests && (
                        <>
                          <Separator />
                          <div>
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-[13px] font-medium text-muted-foreground">AI Tests</span>
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" checked={aiTestsEnabled} onChange={e => setAiTestsEnabled(e.target.checked)} className="rounded text-primary" />
                                <span className="text-xs font-medium">Enable AI</span>
                              </label>
                            </div>

                            {aiTestsEnabled && (
                              <div className="space-y-3">
                                <div className="flex flex-col h-64 min-h-0 rounded-md border bg-background">
                                  <div className="flex-1 overflow-y-auto p-2 space-y-2 text-xs">
                                    {customAiTests.length === 0 ? (
                                      <div className="text-center text-muted-foreground py-8">Ask me to create tests in plain English...</div>
                                    ) : (
                                      customAiTests.map((test, index) => (
                                        <div key={index} className="space-y-1">
                                          <div className="flex justify-end">
                                            <div className="bg-primary/10 text-primary px-2 py-1 rounded text-xs max-w-xs">
                                              {test || 'Empty test...'}
                                              <button
                                                onClick={() => setCustomAiTests(customAiTests.filter((_, i) => i !== index))}
                                                className="ml-1 text-primary/70 hover:text-primary"
                                              >
                                                ✕
                                              </button>
                                            </div>
                                          </div>
                                          <div className="flex justify-start">
                                            <div className="bg-muted text-muted-foreground px-2 py-1 rounded text-xs max-w-xs">Will generate SQL for: &quot;{test.substring(0, 30)}...&quot;</div>
                                          </div>
                                        </div>
                                      ))
                                    )}
                                  </div>
                                  <div className="sticky bottom-0 border-t bg-background p-2 flex gap-2">
                                    <Input
                                      placeholder="Type your test request..."
                                      className="h-8 text-xs flex-1"
                                      onKeyDown={e => {
                                        if (e.key === 'Enter') {
                                          const input = e.currentTarget as HTMLInputElement
                                          if (input.value.trim()) {
                                            setCustomAiTests([...customAiTests, input.value.trim()])
                                            input.value = ''
                                          }
                                        }
                                      }}
                                    />
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      className="h-8 px-2 text-xs"
                                      onClick={e => {
                                        const input = (e.currentTarget.parentElement?.querySelector('input') as HTMLInputElement) || null
                                        if (input?.value.trim()) {
                                          setCustomAiTests([...customAiTests, input.value.trim()])
                                          input.value = ''
                                        }
                                      }}
                                    >
                                      Send
                                    </Button>
                                  </div>
                                </div>
                                <div className="space-y-1">
                                  <div className="text-xs text-muted-foreground">💡 Quick suggestions:</div>
                                  <div className="flex flex-wrap gap-1">
                                    {['Check email formats', 'Find duplicate records', 'Validate age ranges', 'Check data completeness'].map(s => (
                                      <button
                                        key={s}
                                        onClick={() => setCustomAiTests([...customAiTests, s])}
                                        className="text-xs bg-muted/30 hover:bg-muted px-2 py-1 rounded text-muted-foreground"
                                      >
                                        {s}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="upload" className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                      <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                      <div className="space-y-2">
                        <h3 className="text-lg font-medium text-gray-900">Upload Test Data</h3>
                        <p className="text-sm text-gray-500">Support for CSV, JSON, Parquet files up to 100MB</p>
                        <div className="flex justify-center">
                          <label className="cursor-pointer">
                            <Button variant="outline" className="mt-2" asChild>
                              <span>Choose Files</span>
                            </Button>
                            <input type="file" className="hidden" accept=".csv,.json,.parquet" onChange={handleFileUpload} />
                          </label>
                        </div>
                      </div>
                    </div>
                    {uploadedFile && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center space-x-3">
                          <BarChart3 className="h-5 w-5 text-blue-600" />
                          <div>
                            <div className="font-medium text-blue-900">{uploadedFile.name}</div>
                            <div className="text-sm text-blue-600">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          </div>

          {/* Right Panel - Test Execution */}
          <div className="col-span-3 min-h-0 flex flex-col gap-4">
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm">
              <div className="p-3 border-b bg-gray-50/40 rounded-t-2xl">
                <div className="flex items-center gap-2">
                  <Play className="h-4 w-4 text-gray-500" />
                  <span className="text-[13px] font-medium text-gray-600">Execute Tests</span>
                </div>
              </div>
              <div className="p-4 space-y-4">
                <Button
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 rounded-xl font-semibold"
                  size="lg"
                  onClick={handleRunPipeline}
                  disabled={isRunning}
                >
                  {isRunning ? (
                    <>
                      <Clock className="mr-2 h-4 w-4 animate-spin" />
                      Running Tests...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      🚀 Run Tests
                    </>
                  )}
                </Button>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Estimated Duration</span>
                    <span className="font-medium">~3 minutes</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Test Coverage</span>
                    <span className="font-medium">12 tests</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Environment</span>
                    <Badge variant="outline" className="text-xs">Snowflake</Badge>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm flex-1 flex flex-col min-h-0">
              <div className="p-3 border-b bg-gray-50/40 rounded-t-2xl">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-gray-500" />
                  <span className="text-[13px] font-medium text-gray-600">Live Results</span>
                </div>
              </div>
              <div className="p-4 flex-1 overflow-auto">
                {testResults.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <BarChart3 className="mx-auto h-8 w-8 mb-2 text-gray-400" />
                    <p className="text-sm">Run tests to see results</p>
                  </div>
                ) : (
                  <ScrollArea className="h-80">
                    <div className="space-y-3">
                      {testResults.map((result, index) => (
                        <div key={index} className="p-4 border-2 border-gray-100 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              {result.status === 'passed' ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : result.status === 'failed' ? (
                                <AlertCircle className="h-4 w-4 text-red-500" />
                              ) : result.status === 'warning' ? (
                                <AlertCircle className="h-4 w-4 text-yellow-500" />
                              ) : result.status === 'info' ? (
                                <BarChart3 className="h-4 w-4 text-blue-500" />
                              ) : (
                                <Clock className="h-4 w-4 text-gray-500 animate-spin" />
                              )}
                              <span className="text-sm font-medium">{result.name}</span>
                            </div>
                            <span className="text-xs text-gray-500">{result.duration}</span>
                          </div>

                          {result.details && (result.name.includes('Test Summary') || result.name.includes('Hybrid Test Summary')) && (
                            <div className="text-xs space-y-1 bg-blue-50 p-2 rounded">
                              {result.name.includes('Hybrid') ? (
                                <>
                                  <div>Total Tests: <strong>{result.details.total_tests}</strong></div>
                                  <div>⚡ Static: {result.details.static_tests} | 🤖 AI: {result.details.ai_tests}</div>
                                  <div>✅ Passed: {result.details.passed} | ❌ Failed: {result.details.failed}</div>
                                  {result.details.ai_cost > 0 && <div>💰 AI Cost: <strong>${result.details.ai_cost.toFixed(4)}</strong> ({result.details.ai_tokens} tokens)</div>}
                                </>
                              ) : (
                                <>
                                  <div>Quality Score: <strong>{result.details.quality_score}%</strong></div>
                                  <div>Tests: {result.details.passed}/{result.details.total_tests} passed</div>
                                </>
                              )}
                              {(result.details?.html_report_url || result.html_report_url) && (
                                <div>
                                  <a 
                                    href={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${result.details?.html_report_url || result.html_report_url}`} 
                                    target="_blank" 
                                    rel="noopener noreferrer" 
                                    className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 underline text-sm font-medium"
                                  >
                                    📄 View HTML Report
                                  </a>
                                </div>
                              )}
                            </div>
                          )}

                          {Array.isArray(result.issues) && result.issues.length > 0 && (
                            <div className="text-xs space-y-1">
                              {result.issues.map((issue: string, i: number) => (
                                <div key={i} className="text-orange-600 bg-orange-50 p-1 rounded">⚠️ {issue}</div>
                              ))}
                            </div>
                          )}

                          {result.details && !result.name.includes('Test Summary') && !result.name.includes('Hybrid Test Summary') && (
                            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                              {result.source === 'ai' ? (
                                <>
                                  {result.details.explanation && <div className="mb-2 text-blue-700">💡 {result.details.explanation}</div>}
                                  {result.details.sql && <div className="font-mono text-xs bg-gray-800 text-green-400 p-2 rounded">{result.details.sql}</div>}
                                  {result.details.tokens && <div className="mt-1">🤖 {result.details.tokens} tokens | {result.details.provider}</div>}
                                </>
                              ) : (
                                Object.entries(result.details).map(([key, value]) => (
                                  <div key={key}>{key.replace(/_/g, ' ')}: {String(value)}</div>
                                ))
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}

                {testResults.length > 0 && (
                  <div className="mt-4 pt-3 border-t">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center space-x-1">
                        <CheckCircle className="h-3 w-3 text-green-500" />
                        <span>Passed: {testResults.filter(r => r.status === 'passed').length}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <AlertCircle className="h-3 w-3 text-red-500" />
                        <span>Failed: {testResults.filter(r => r.status === 'failed').length}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
    </QueryClientProvider>
  )
}
