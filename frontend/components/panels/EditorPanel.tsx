'use client'

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useWorkspaceStore } from '@/stores/workspace'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Code, Zap, AlertCircle, RotateCcw, Trash2 } from 'lucide-react'
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

  const handleClear = () => {
    setBuilderText('')
  }

  const handleFormat = () => {
    // Basic SQL formatting - in production would use a proper formatter
    if (builderText) {
      const formatted = builderText
        .replace(/\bSELECT\b/gi, '\nSELECT')
        .replace(/\bFROM\b/gi, '\nFROM')
        .replace(/\bWHERE\b/gi, '\nWHERE')
        .replace(/\bORDER BY\b/gi, '\nORDER BY')
        .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
        .trim()
      setBuilderText(formatted)
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tight Toolbar */}
      <div className="h-10 border-b bg-muted/10 flex items-center justify-between px-3" style={{ gap: 'var(--gap-2)' }}>
        <div className="flex items-center" style={{ gap: 'var(--gap-1)' }}>
          <Code className="h-3 w-3 text-muted-foreground" />
          <span className="text-xs font-medium">SQL Editor</span>
          {hasSelection && (
            <Badge variant="secondary" className="text-xs h-4 px-1">
              {selectedCount}
            </Badge>
          )}
        </div>
        
        <div className="flex items-center" style={{ gap: 'var(--gap-1)' }}>
          <Button 
            onClick={handleCompileSelected}
            disabled={!hasSelection || isCompiling}
            size="sm"
            className="h-6 px-2 text-xs"
          >
            <Zap className="h-3 w-3 mr-1" />
            {isCompiling ? 'Compiling...' : 'Compile'}
          </Button>
          <Button 
            onClick={handleFormat}
            disabled={!builderText}
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
          >
            <RotateCcw className="h-3 w-3" />
          </Button>
          <Button 
            onClick={handleClear}
            disabled={!builderText}
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>
      
      {/* Compilation Status */}
      {compileTestMutation.isError && (
        <div className="mx-3 my-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-xs">
          <div className="flex items-center" style={{ gap: 'var(--gap-1)' }}>
            <AlertCircle className="h-3 w-3 text-destructive" />
            <span className="text-destructive">
              Compilation failed: {compileTestMutation.error?.message}
            </span>
          </div>
        </div>
      )}
      
      {/* Monaco Editor */}
      <div className="flex-1">
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
            fontSize: 13,
            lineNumbers: 'on',
            roundedSelection: false,
            wordWrap: 'on',
            automaticLayout: true,
            scrollbar: {
              vertical: 'visible',
              horizontal: 'visible',
            },
            padding: {
              top: 8,
              bottom: 8,
            },
          }}
        />
      </div>
      
      {/* Editor Footer */}
      <div className="h-6 px-3 border-t bg-muted/30 text-xs text-muted-foreground flex items-center justify-between">
        <span>
          {builderText ? `${builderText.split('\n').length} lines` : 'No content'}
        </span>
        <span>SQL</span>
      </div>
    </div>
  )
}
