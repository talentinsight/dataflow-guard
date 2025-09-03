'use client'

import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { StatusChip } from '@/components/common/StatusChip'
import { 
  Database, 
  Upload, 
  Play, 
  ArrowRight, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  BarChart3,
  Zap,
  GitBranch,
  Clock,
  Target,
  Folder,
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
  const [costEstimate, setCostEstimate] = useState<any>(null)
  const [databases, setDatabases] = useState<any[]>([])
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [loadingNodes, setLoadingNodes] = useState<Set<string>>(new Set())

  // Load databases on mount
  useEffect(() => {
    loadDatabases()
  }, [])

  const loadDatabases = async () => {
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/api/v1/metadata/databases`)
      const data = await response.json()
      setDatabases(data.databases || [])
    } catch (error) {
      console.error('Failed to load databases:', error)
      setDatabases([]) // Set empty array on error
    }
  }

  const loadSchemas = async (databaseName: string) => {
    const nodeKey = `db:${databaseName}`
    setLoadingNodes(prev => new Set([...Array.from(prev), nodeKey]))
    
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/api/v1/metadata/schemas/${databaseName}`)
      const data = await response.json()
      
      // Update database with schemas
      setDatabases(prev => prev.map(db => 
        db.DATABASE_NAME === databaseName 
          ? { ...db, schemas: data.schemas || [] }
          : db
      ))
    } catch (error) {
      console.error('Failed to load schemas:', error)
    } finally {
      setLoadingNodes(prev => {
        const newSet = new Set(prev)
        newSet.delete(nodeKey)
        return newSet
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
      
      // Update schema with tables
      setDatabases(prev => prev.map(db => 
        db.DATABASE_NAME === databaseName 
          ? {
              ...db,
              schemas: db.schemas?.map((schema: any) => 
                schema.SCHEMA_NAME === schemaName
                  ? { ...schema, tables: data.tables || [] }
                  : schema
              )
            }
          : db
      ))
    } catch (error) {
      console.error('Failed to load tables:', error)
    } finally {
      setLoadingNodes(prev => {
        const newSet = new Set(prev)
        newSet.delete(nodeKey)
        return newSet
      })
    }
  }

  const toggleNode = (nodeKey: string, databaseName?: string, schemaName?: string) => {
    const isExpanded = expandedNodes.has(nodeKey)
    
    if (isExpanded) {
      setExpandedNodes(prev => {
        const newSet = new Set(prev)
        newSet.delete(nodeKey)
        return newSet
      })
    } else {
      setExpandedNodes(prev => new Set([...Array.from(prev), nodeKey]))
      
      // Load data if needed
      if (nodeKey.startsWith('db:') && databaseName) {
        const db = databases.find(d => d.DATABASE_NAME === databaseName)
        if (!db?.schemas) {
          loadSchemas(databaseName)
        }
      } else if (nodeKey.startsWith('schema:') && databaseName && schemaName) {
        const db = databases.find(d => d.DATABASE_NAME === databaseName)
        const schema = db?.schemas?.find((s: any) => s.SCHEMA_NAME === schemaName)
        if (!schema?.tables) {
          loadTables(databaseName, schemaName)
        }
      }
    }
  }

  const selectTable = (databaseName: string, schemaName: string, tableName: string) => {
    const fullTableName = `${databaseName}.${schemaName}.${tableName}`
    
    // Auto-fill based on schema pattern
    if (schemaName.toUpperCase().includes('RAW')) {
      const sourceInput = document.querySelector('input[placeholder="Select from browser above"]') as HTMLInputElement
      if (sourceInput) sourceInput.value = fullTableName
    } else if (schemaName.toUpperCase().includes('PREP')) {
      const prepInput = document.querySelector('input[placeholder="Select prep table from browser"]') as HTMLInputElement
      if (prepInput) prepInput.value = fullTableName
    } else if (schemaName.toUpperCase().includes('MART')) {
      const martInput = document.querySelector('input[placeholder="Select mart table from browser"]') as HTMLInputElement
      if (martInput) martInput.value = fullTableName
    } else {
      // Default to source if unclear
      const sourceInput = document.querySelector('input[placeholder="Select from browser above"]') as HTMLInputElement
      if (sourceInput) sourceInput.value = fullTableName
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  const handleRunPipeline = async () => {
    setIsRunning(true)
    setTestResults([])
    
    try {
      // Start real ETL pipeline
      // Get values from inputs
      const sourceTableInput = document.querySelector('input[placeholder="Select from browser above"]') as HTMLInputElement;
      const prepTableInput = document.querySelector('input[placeholder="Select prep table from browser"]') as HTMLInputElement;
      const martTableInput = document.querySelector('input[placeholder="Select mart table from browser"]') as HTMLInputElement;
      
      const sourceTable = sourceTableInput?.value;
      const prepTable = prepTableInput?.value;
      const martTable = martTableInput?.value;
      
      // Validate inputs
      if (!sourceTable || sourceTable.trim() === '') {
        setTestResults([{ status: 'error', message: 'Please select a source table from the database browser.' }]);
        setIsRunning(false);
        return;
      }
      
      if (!prepTable || prepTable.trim() === '') {
        setTestResults([{ status: 'error', message: 'Please select a prep table from the database browser.' }]);
        setIsRunning(false);
        return;
      }
      
      if (!martTable || martTable.trim() === '') {
        setTestResults([{ status: 'error', message: 'Please select a mart table from the database browser.' }]);
        setIsRunning(false);
        return;
      }
      
      // Parse source table
      const parts = sourceTable.split('.');
      const sourceSchema = parts.slice(0, 2).join('.');
      const tableName = parts[parts.length - 1];
      
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      
      // Use Hybrid Test Engine if enabled
      const endpoint = useHybridTests ? '/api/v1/hybrid/test' : '/api/v1/pipeline/test/v2'
      const requestBody = useHybridTests ? {
        source_table: sourceTable,
        prep_table: prepTable,
        mart_table: martTable,
        test_types: ['row_count', 'null_check', 'email_format', 'transformation_accuracy'],
        natural_language_tests: aiTestsEnabled ? customAiTests.filter(test => test.trim()) : [],
        use_ai_fallback: aiTestsEnabled
      } : {
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
      
      // Handle Hybrid Test results (immediate response)
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
          // Add static test results
          ...result.static_results?.map((test: any) => ({
            name: `⚡ ${test.test_name}`,
            status: test.status === 'pass' ? 'passed' : test.status === 'fail' ? 'failed' : 'warning',
            duration: 'Static',
            details: test.raw_results,
            source: 'static'
          })) || [],
          // Add AI test results
          ...result.ai_results?.map((test: any) => ({
            name: `🤖 ${test.test_name}`,
            status: test.status === 'pass' ? 'passed' : test.status === 'fail' ? 'failed' : 'warning',
            duration: `${test.tokens || 0} tokens`,
            details: {
              sql: test.generated_sql,
              explanation: test.explanation,
              tokens: test.tokens,
              provider: test.provider
            },
            source: 'ai'
          })) || []
        ]
        
        setTestResults(hybridResults)
        setIsRunning(false)
        return
      }
      
      // Legacy polling for non-hybrid tests
      const runId = result.run_id
      
      // Poll for status updates
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(`${apiBaseUrl}/api/v1/pipeline/test/v2/${runId}`)
          const status = await statusResponse.json()
          
          // Handle comprehensive test results
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
                  html_report_url: `${apiBaseUrl}/api/v1/pipeline/test/v2/${runId}/report/html`
                }
              },
              ...status.comprehensive_results.test_results.map((test: any) => ({
                name: test.test_name,
                status: test.status === 'pass' ? 'passed' : test.status === 'fail' ? 'failed' : 'warning',
                duration: 'Completed',
                details: test.metrics,
                issues: test.issues
              }))
            ]
            setTestResults(comprehensiveResults)
          } else {
            // Show basic status while running
            const basicResults = [{
              name: status.current_step || 'Initializing',
              status: 'running',
              duration: 'Running...'
            }]
            setTestResults(basicResults)
          }
          
          if (status.status === 'completed' || status.status === 'failed') {
            setIsRunning(false)
            return
          }
          
          // Continue polling
          setTimeout(pollStatus, 2000)
        } catch (error) {
          console.error('Polling error:', error)
          setIsRunning(false)
        }
      }
      
      // Start polling
      setTimeout(pollStatus, 1000)
      
    } catch (error) {
      console.error('Pipeline start error:', error)
      setIsRunning(false)
      setTestResults([
        { name: 'Pipeline Start', status: 'failed', duration: '0s' }
      ])
    }
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Clean Professional Header */}
        <header className="bg-white border-b px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Zap className="h-6 w-6 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">DataFlowGuard</h1>
              <Badge variant="outline" className="text-xs font-medium">ETL Pipeline Testing</Badge>
            </div>
            <div className="flex items-center space-x-4">
              <StatusChip />
              <Badge className="bg-green-100 text-green-800 border-green-200">
                Snowflake Connected
              </Badge>
            </div>
          </div>
        </header>

        {/* Main Content - Spacious 3-Column Layout */}
        <div className="flex-1 grid grid-cols-12 gap-8 p-8">
          
          {/* Left: Pipeline Configuration */}
          <div className="col-span-3">
            <Card className="h-full shadow-lg border-0 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-lg">
                <CardTitle className="flex items-center text-lg font-semibold">
                  <GitBranch className="mr-2 h-5 w-5 text-blue-600" />
                  Pipeline Setup
                </CardTitle>
                <CardDescription className="text-gray-600">Configure your ETL data flow</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 p-6">
                
                {/* Database Browser - Compact */}
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm text-gray-800">Database Browser</h4>
                  
                  <div className="border rounded-lg p-2 bg-gray-50 max-h-48 overflow-y-auto text-xs">
                    <div className="space-y-1 text-xs">
                      {databases.map((database) => {
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
                              <span className="font-medium text-gray-800">
                                {database.DATABASE_NAME}
                              </span>
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
                                        <span className="text-gray-600">
                                          {schema.SCHEMA_NAME}
                                        </span>
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
                          Loading databases...
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div>
                      <label className="text-xs font-medium text-gray-600 mb-1 block">Source Table</label>
                      <Input 
                        placeholder="Select from browser above" 
                        className="text-xs h-8"
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs font-medium text-gray-600 mb-1 block">Prep Table</label>
                      <Input 
                        placeholder="Select prep table from browser" 
                        className="text-xs h-8"
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs font-medium text-gray-600 mb-1 block">Mart Table</label>
                      <Input 
                        placeholder="Select mart table from browser" 
                        className="text-xs h-8"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Center: Test Configuration */}
          <div className="col-span-6">
            <Card className="h-full shadow-lg border-0 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="pb-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-t-lg">
                <CardTitle className="flex items-center text-lg font-semibold">
                  <Upload className="mr-2 h-5 w-5 text-green-600" />
                  Test Configuration
                </CardTitle>
                <CardDescription className="text-gray-600">Configure validation rules and AI tests</CardDescription>
              </CardHeader>
              <CardContent className="p-6 h-full overflow-auto">
                
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 mb-6 bg-gray-100 p-1 rounded-lg">
                    <TabsTrigger value="validation" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
                      🚀 Test Rules
                    </TabsTrigger>
                    <TabsTrigger value="upload" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
                      📁 Data Upload
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="validation" className="space-y-6">
                      <div className="space-y-6">
                        
                        {/* Test Engine Selection - Modern Cards */}
                        <div>
                          <h4 className="font-semibold text-base mb-4 text-gray-800">Choose Test Engine</h4>
                          <div className="grid grid-cols-2 gap-4">
                            <label className={`relative cursor-pointer p-4 rounded-xl border-2 transition-all ${
                              useHybridTests 
                                ? 'border-blue-500 bg-blue-50 shadow-md' 
                                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                            }`}>
                              <input 
                                type="radio" 
                                name="testEngine" 
                                checked={useHybridTests}
                                onChange={() => setUseHybridTests(true)}
                                className="sr-only" 
                              />
                              <div className="text-center">
                                <div className="text-2xl mb-2">🚀</div>
                                <div className="font-semibold text-sm text-gray-800">Hybrid Engine</div>
                                <div className="text-xs text-gray-600 mt-1">Smart + Fast</div>
                                {useHybridTests && (
                                  <div className="absolute top-2 right-2">
                                    <CheckCircle className="h-4 w-4 text-blue-500" />
                                  </div>
                                )}
                              </div>
                            </label>
                            <label className={`relative cursor-pointer p-4 rounded-xl border-2 transition-all ${
                              !useHybridTests 
                                ? 'border-green-500 bg-green-50 shadow-md' 
                                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                            }`}>
                              <input 
                                type="radio" 
                                name="testEngine" 
                                checked={!useHybridTests}
                                onChange={() => setUseHybridTests(false)}
                                className="sr-only" 
                              />
                              <div className="text-center">
                                <div className="text-2xl mb-2">⚡</div>
                                <div className="font-semibold text-sm text-gray-800">Legacy Engine</div>
                                <div className="text-xs text-gray-600 mt-1">Static Only</div>
                                {!useHybridTests && (
                                  <div className="absolute top-2 right-2">
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  </div>
                                )}
                              </div>
                            </label>
                          </div>
                        </div>
                        
                        <Separator />
                        
                        {/* Static Tests - Modern Grid */}
                        <div>
                          <h4 className="font-semibold text-base mb-4 text-gray-800 flex items-center">
                            ⚡ Static Tests 
                            {useHybridTests && <Badge variant="outline" className="ml-2 text-xs">Free & Fast</Badge>}
                          </h4>
                          <div className="grid grid-cols-3 gap-3">
                            {[
                              { name: 'Row Count', icon: '📊' },
                              { name: 'NULL Detection', icon: '🔍' }, 
                              { name: 'Email Format', icon: '📧' },
                              { name: 'Transformation', icon: '🔄' },
                              { name: 'Duplicates', icon: '👥' },
                              { name: 'Schema', icon: '🏗️' }
                            ].map((test) => (
                              <label key={test.name} className="flex items-center space-x-2 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors">
                                <input type="checkbox" className="rounded text-blue-600" defaultChecked />
                                <span className="text-lg">{test.icon}</span>
                                <span className="text-sm font-medium text-gray-700">{test.name}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                        
                        {useHybridTests && (
                          <>
                            <Separator />
                            
                            {/* AI Tests - Modern Design */}
                            <div>
                              <div className="flex items-center justify-between mb-4">
                                <h4 className="font-semibold text-base text-gray-800 flex items-center">
                                  🤖 AI Tests 
                                  <Badge variant="outline" className="ml-2 text-xs bg-orange-50 text-orange-700 border-orange-200">Smart & Paid</Badge>
                                </h4>
                                <label className="flex items-center space-x-2 cursor-pointer">
                                  <input 
                                    type="checkbox" 
                                    checked={aiTestsEnabled}
                                    onChange={(e) => setAiTestsEnabled(e.target.checked)}
                                    className="rounded text-blue-600" 
                                  />
                                  <span className="text-sm font-medium text-gray-700">Enable AI</span>
                                </label>
                              </div>
                              
                              {aiTestsEnabled && (
                                <div className="space-y-3">
                                  <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
                                    💬 Chat with AI to create custom tests
                                  </div>
                                  
                                  {/* Chat-like AI Test Interface - Compact */}
                                  <div className="border border-gray-200 rounded-lg bg-white">
                                    {/* Chat Messages */}
                                    <div className="max-h-32 overflow-y-auto p-3 space-y-2">
                                      {customAiTests.length === 0 ? (
                                        <div className="text-xs text-gray-500 italic text-center py-2">
                                          🤖 Ask me to create tests in plain English...
                                        </div>
                                      ) : (
                                        customAiTests.map((test, index) => (
                                          <div key={index} className="space-y-1">
                                            {/* User Message */}
                                            <div className="flex justify-end">
                                              <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg text-xs max-w-xs">
                                                {test || "Empty test..."}
                                                <button
                                                  onClick={() => {
                                                    const newTests = customAiTests.filter((_, i) => i !== index)
                                                    setCustomAiTests(newTests)
                                                  }}
                                                  className="ml-2 text-blue-600 hover:text-blue-800"
                                                >
                                                  ✕
                                                </button>
                                              </div>
                                            </div>
                                            {/* AI Response Preview */}
                                            <div className="flex justify-start">
                                              <div className="bg-gray-100 text-gray-700 px-3 py-1 rounded-lg text-xs max-w-xs">
                                                🤖 Will generate SQL for: &quot;{test.substring(0, 30)}...&quot;
                                              </div>
                                            </div>
                                          </div>
                                        ))
                                      )}
                                    </div>
                                    
                                    {/* Chat Input */}
                                    <div className="border-t p-2">
                                      <div className="flex space-x-2">
                                        <Input
                                          placeholder="💬 Type your test request... (e.g., 'Check if all emails are valid')"
                                          className="text-sm flex-1"
                                          onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                              const input = e.target as HTMLInputElement
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
                                          onClick={(e) => {
                                            const input = (e.target as HTMLElement).previousElementSibling as HTMLInputElement
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
                                  </div>
                                  
                                  {/* Quick Suggestions */}
                                  <div className="space-y-1">
                                    <div className="text-xs text-gray-600">💡 Quick suggestions:</div>
                                    <div className="flex flex-wrap gap-1">
                                      {[
                                        "Check email formats",
                                        "Find duplicate records", 
                                        "Validate age ranges",
                                        "Check data completeness"
                                      ].map((suggestion) => (
                                        <button
                                          key={suggestion}
                                          onClick={() => setCustomAiTests([...customAiTests, suggestion])}
                                          className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded text-gray-700"
                                        >
                                          {suggestion}
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
                        <p className="text-sm text-gray-500">
                          Support for CSV, JSON, Parquet files up to 100MB
                        </p>
                        <div className="flex justify-center">
                          <label className="cursor-pointer">
                            <Button variant="outline" className="mt-2" asChild>
                              <span>Choose Files</span>
                            </Button>
                            <input 
                              type="file" 
                              className="hidden" 
                              accept=".csv,.json,.parquet"
                              onChange={handleFileUpload}
                            />
                          </label>
                        </div>
                      </div>
                    </div>
                    
                    {uploadedFile && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center space-x-3">
                          <FileText className="h-5 w-5 text-blue-600" />
                          <div>
                            <div className="font-medium text-blue-900">{uploadedFile.name}</div>
                            <div className="text-sm text-blue-600">
                              {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right: Test Execution & Results */}
          <div className="col-span-3 flex flex-col gap-6">
            
            {/* Execution Control */}
            <Card className="shadow-lg border-0 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="pb-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-t-lg">
                <CardTitle className="flex items-center text-lg font-semibold">
                  <Play className="mr-2 h-5 w-5 text-purple-600" />
                  Execute Tests
                </CardTitle>
                <CardDescription className="text-gray-600">Run your pipeline validation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 p-6">
                  <Button 
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg" 
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
                </CardContent>
              </Card>

            {/* Live Results */}
            <Card className="flex-1 shadow-lg border-0 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-t-lg">
                <CardTitle className="flex items-center text-lg font-semibold">
                  <BarChart3 className="mr-2 h-5 w-5 text-blue-600" />
                  Live Results
                </CardTitle>
                <CardDescription className="text-gray-600">Real-time test execution results</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
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
                            
                            {/* Show details for summary */}
                            {result.details && (result.name.includes('Test Summary') || result.name.includes('Hybrid Test Summary')) && (
                              <div className="text-xs space-y-1 bg-blue-50 p-2 rounded">
                                {result.name.includes('Hybrid') ? (
                                  <>
                                    <div>Total Tests: <strong>{result.details.total_tests}</strong></div>
                                    <div>⚡ Static: {result.details.static_tests} | 🤖 AI: {result.details.ai_tests}</div>
                                    <div>✅ Passed: {result.details.passed} | ❌ Failed: {result.details.failed}</div>
                                    {result.details.ai_cost > 0 && (
                                      <div>💰 AI Cost: <strong>${result.details.ai_cost.toFixed(4)}</strong> ({result.details.ai_tokens} tokens)</div>
                                    )}
                                  </>
                                ) : (
                                  <>
                                    <div>Quality Score: <strong>{result.details.quality_score}%</strong></div>
                                    <div>Tests: {result.details.passed}/{result.details.total_tests} passed</div>
                                  </>
                                )}
                                {result.details.html_report_url && (
                                  <div>
                                    <a 
                                      href={result.details.html_report_url} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:text-blue-800 underline"
                                    >
                                      📄 View HTML Report
                                    </a>
                                  </div>
                                )}
                              </div>
                            )}
                            
                            {/* Show issues if any */}
                            {result.issues && result.issues.length > 0 && (
                              <div className="text-xs space-y-1">
                                {result.issues.map((issue: string, i: number) => (
                                  <div key={i} className="text-orange-600 bg-orange-50 p-1 rounded">
                                    ⚠️ {issue}
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {/* Show metrics if available */}
                            {result.details && !result.name.includes('Test Summary') && !result.name.includes('Hybrid Test Summary') && (
                              <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                                {result.source === 'ai' ? (
                                  <>
                                    {result.details.explanation && (
                                      <div className="mb-2 text-blue-700">💡 {result.details.explanation}</div>
                                    )}
                                    {result.details.sql && (
                                      <div className="font-mono text-xs bg-gray-800 text-green-400 p-2 rounded">
                                        {result.details.sql}
                                      </div>
                                    )}
                                    {result.details.tokens && (
                                      <div className="mt-1">🤖 {result.details.tokens} tokens | {result.details.provider}</div>
                                    )}
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
                </CardContent>
              </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </QueryClientProvider>
  )
}
