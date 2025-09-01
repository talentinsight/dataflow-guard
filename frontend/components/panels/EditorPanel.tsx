'use client'

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useWorkspaceStore } from '@/stores/workspace'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Code, Zap, AlertCircle } from 'lucide-react'
import dynamic from 'next/dynamic'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

export function EditorPanel() {
  const { 
    builderText, 
    setBuilderText, 
    selectedTests, 
    getSelectedTestCount 
  } = useWorkspaceStore()

  const compileTestMutation = useMutation({
    mutationFn: (testData: any) => apiClient.compileTest(testData),
    onSuccess: (data) => {
      setBuilderText(data.sql || '-- Compiled SQL will appear here')
    },
    onError: (error) => {
      setBuilderText(`-- Compilation failed: ${error.message}\n-- Please check your test selection and try again`)
    }
  })

  const handleCompileSelected = () => {
    if (getSelectedTestCount() === 0) {
      setBuilderText('-- Please select at least one test from the Plan panel to compile')
      return
    }

    // Convert selected test IDs to test objects for compilation
    const selectedTestIds = Array.from(selectedTests)
    compileTestMutation.mutate({
      tests: selectedTestIds.map(id => ({ id, name: `Test ${id}` })),
      dataset: 'SAMPLE.TABLE', // This would come from dataset panel
    })
  }

  const selectedCount = getSelectedTestCount()
  const hasSelection = selectedCount > 0
  const isCompiling = compileTestMutation.isPending

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Code className="h-4 w-4" />
            <div>
              <CardTitle className="text-base">SQL Editor</CardTitle>
              <CardDescription className="text-sm">AI-compiled SQL from your test selections</CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {hasSelection && (
              <Badge variant="secondary" className="text-xs">
                {selectedCount} test{selectedCount !== 1 ? 's' : ''}
              </Badge>
            )}
            <Button 
              onClick={handleCompileSelected}
              disabled={!hasSelection || isCompiling}
              size="sm"
            >
              <Zap className="mr-2 h-3 w-3" />
              {isCompiling ? 'Compiling...' : 'Compile'}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        {/* Compilation Status */}
        {compileTestMutation.isError && (
          <div className="mx-4 mb-3 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <span className="text-sm text-destructive">
                Compilation failed: {compileTestMutation.error?.message}
              </span>
            </div>
          </div>
        )}
        
        {/* Monaco Editor */}
        <div className="flex-1 border-t">
          <MonacoEditor
            height="100%"
            language="sql"
            theme="vs-light"
            value={builderText || '-- Select tests from the Plan panel and click "Compile" to generate SQL'}
            onChange={(value) => setBuilderText(value || '')}
            options={{
              readOnly: false,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 14,
              lineNumbers: 'on',
              roundedSelection: false,
              wordWrap: 'on',
              automaticLayout: true,
              scrollbar: {
                vertical: 'visible',
                horizontal: 'visible',
              },
              padding: {
                top: 16,
                bottom: 16,
              },
            }}
          />
        </div>
        
        {/* Editor Footer */}
        <div className="px-4 py-2 border-t bg-muted/30 text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>
              {builderText ? `${builderText.split('\n').length} lines` : 'No content'}
            </span>
            <span>SQL</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
