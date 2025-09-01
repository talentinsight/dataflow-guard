'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useTestSelectionStore } from '@/lib/stores/testSelectionStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Checkbox } from '@/components/ui/checkbox'
import { Play, TestTube, Database, Clock, CheckCircle } from 'lucide-react'
import dynamic from 'next/dynamic'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

export default function BuilderPage() {
  const [activeTab, setActiveTab] = useState('templates')
  const [editorValue, setEditorValue] = useState('')
  
  const { 
    selectedTestIds, 
    toggleTestSelection, 
    clearSelection, 
    getSelectedCount,
    isSelected 
  } = useTestSelectionStore()

  // Mock test templates
  const testTemplates = [
    {
      id: 'data-quality',
      name: 'Data Quality Check',
      description: 'Validate data completeness and accuracy',
      icon: <CheckCircle className="h-5 w-5" />,
      category: 'Quality',
      tests: [
        { id: 'null-check', name: 'Null Value Check', description: 'Check for unexpected null values' },
        { id: 'duplicate-check', name: 'Duplicate Detection', description: 'Identify duplicate records' },
        { id: 'range-check', name: 'Value Range Validation', description: 'Ensure values are within expected ranges' },
      ]
    },
    {
      id: 'schema-validation',
      name: 'Schema Validation',
      description: 'Check column types and constraints',
      icon: <Database className="h-5 w-5" />,
      category: 'Schema',
      tests: [
        { id: 'type-check', name: 'Data Type Validation', description: 'Verify column data types' },
        { id: 'constraint-check', name: 'Constraint Validation', description: 'Check primary key and foreign key constraints' },
        { id: 'column-check', name: 'Column Existence', description: 'Ensure required columns exist' },
      ]
    },
    {
      id: 'freshness-check',
      name: 'Data Freshness',
      description: 'Monitor data update frequency',
      icon: <Clock className="h-5 w-5" />,
      category: 'Freshness',
      tests: [
        { id: 'last-update', name: 'Last Update Check', description: 'Verify data was updated recently' },
        { id: 'batch-freshness', name: 'Batch Freshness', description: 'Check if latest batch is within SLA' },
      ]
    }
  ]

  const compileTestMutation = useMutation({
    mutationFn: (testData: any) => apiClient.compileTest(testData),
    onSuccess: (data) => {
      setEditorValue(data.sql || '-- Compiled SQL will appear here')
    }
  })

  const handleCompileSelected = () => {
    const selectedTests = testTemplates.flatMap(template => 
      template.tests.filter(test => isSelected(test.id))
    )
    
    if (selectedTests.length === 0) {
      alert('Please select at least one test to compile')
      return
    }

    compileTestMutation.mutate({
      tests: selectedTests,
      dataset: 'SAMPLE.TABLE', // This would come from a dataset selector
    })
  }

  const handleRunTests = () => {
    if (getSelectedCount() === 0) {
      alert('Please select at least one test to run')
      return
    }
    
    // This would trigger the actual test run
    alert(`Running ${getSelectedCount()} selected tests...`)
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between space-y-2 mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Test Builder</h1>
          <p className="text-muted-foreground">Create and configure data quality tests</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary">
            {getSelectedCount()} test{getSelectedCount() !== 1 ? 's' : ''} selected
          </Badge>
          <Button variant="outline" onClick={clearSelection} disabled={getSelectedCount() === 0}>
            Clear Selection
          </Button>
          <Button onClick={handleRunTests} disabled={getSelectedCount() === 0}>
            <Play className="mr-2 h-4 w-4" />
            Run Selected Tests
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Test Selection */}
        <div className="space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="templates">Templates</TabsTrigger>
              <TabsTrigger value="custom">Custom</TabsTrigger>
            </TabsList>
            
            <TabsContent value="templates" className="space-y-4">
              {testTemplates.map((template) => (
                <Card key={template.id}>
                  <CardHeader>
                    <div className="flex items-center space-x-3">
                      {template.icon}
                      <div>
                        <CardTitle className="text-lg">{template.name}</CardTitle>
                        <CardDescription>{template.description}</CardDescription>
                      </div>
                      <Badge variant="outline">{template.category}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {template.tests.map((test) => (
                        <div key={test.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                          <Checkbox
                            checked={isSelected(test.id)}
                            onCheckedChange={() => toggleTestSelection(test.id)}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <h4 className="font-medium">{test.name}</h4>
                            <p className="text-sm text-muted-foreground">{test.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
            
            <TabsContent value="custom">
              <Card>
                <CardHeader>
                  <CardTitle>Custom Test Definition</CardTitle>
                  <CardDescription>Write your own test logic using natural language or formulas</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Test Name</label>
                      <input 
                        className="w-full mt-1 px-3 py-2 border rounded-md"
                        placeholder="Enter test name..."
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Test Description</label>
                      <textarea 
                        className="w-full mt-1 px-3 py-2 border rounded-md"
                        rows={3}
                        placeholder="Describe what this test should validate..."
                      />
                    </div>
                    <Button className="w-full">
                      <TestTube className="mr-2 h-4 w-4" />
                      Add Custom Test
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Panel - Code Editor */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Generated SQL</CardTitle>
                  <CardDescription>AI-compiled SQL from your test selections</CardDescription>
                </div>
                <Button 
                  onClick={handleCompileSelected}
                  disabled={getSelectedCount() === 0 || compileTestMutation.isPending}
                >
                  {compileTestMutation.isPending ? 'Compiling...' : 'Compile Tests'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="border rounded-md overflow-hidden">
                <MonacoEditor
                  height="400px"
                  language="sql"
                  theme="vs-light"
                  value={editorValue || '-- Select tests and click "Compile Tests" to generate SQL'}
                  onChange={(value) => setEditorValue(value || '')}
                  options={{
                    readOnly: false,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    lineNumbers: 'on',
                    roundedSelection: false,
                    scrollbar: {
                      vertical: 'visible',
                      horizontal: 'visible',
                    },
                  }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Test Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Test Configuration</CardTitle>
              <CardDescription>Configure test execution parameters</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Target Dataset</label>
                  <select className="w-full mt-1 px-3 py-2 border rounded-md">
                    <option>SAMPLE.ORDERS</option>
                    <option>SAMPLE.CUSTOMERS</option>
                    <option>SAMPLE.PRODUCTS</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Execution Mode</label>
                  <select className="w-full mt-1 px-3 py-2 border rounded-md">
                    <option>Push-down (Recommended)</option>
                    <option>Local Processing</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="save-suite" />
                  <label htmlFor="save-suite" className="text-sm">Save as test suite</label>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
