'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useWorkspaceStore } from '@/stores/workspace'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { EmptyState } from '@/components/common/EmptyState'
import { Search, TestTube, CheckCircle, Database, Clock, FolderOpen, X } from 'lucide-react'

// Mock test templates (extracted from existing builder page)
const testTemplates = [
  {
    id: 'data-quality',
    name: 'Data Quality Check',
    description: 'Validate data completeness and accuracy',
    icon: <CheckCircle className="h-4 w-4" />,
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
    icon: <Database className="h-4 w-4" />,
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
    icon: <Clock className="h-4 w-4" />,
    category: 'Freshness',
    tests: [
      { id: 'last-update', name: 'Last Update Check', description: 'Verify data was updated recently' },
      { id: 'batch-freshness', name: 'Batch Freshness', description: 'Check if latest batch is within SLA' },
    ]
  }
]

export function PlanPanel() {
  const [searchQuery, setSearchQuery] = useState('')
  const { 
    selectedTests, 
    toggleTestSelection, 
    clearTestSelection, 
    isTestSelected, 
    getSelectedTestCount 
  } = useWorkspaceStore()

  // Query for test suites (graceful fallback to templates)
  const { data: suites, isLoading } = useQuery({
    queryKey: ['suites'],
    queryFn: apiClient.getSuites,
    retry: false,
  })

  // Filter tests based on search query
  const filteredTemplates = testTemplates.map(template => ({
    ...template,
    tests: template.tests.filter(test =>
      test.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      test.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(template => template.tests.length > 0)

  const allTests = testTemplates.flatMap(template => template.tests)
  const selectedCount = getSelectedTestCount()

  return (
    <div className="h-full flex flex-col">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="p-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold">Test Planning</h2>
            {selectedCount > 0 && (
              <Badge variant="secondary" className="text-xs h-5">
                {selectedCount}
              </Badge>
            )}
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="Search tests..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-7 h-8 text-xs"
            />
          </div>
          
          {/* Selected Count & Clear */}
          {selectedCount > 0 && (
            <>
              <Separator className="my-2" />
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {selectedCount} selected
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearTestSelection}
                  className="h-6 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              </div>
            </>
          )}
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : filteredTemplates.length === 0 ? (
          <EmptyState
            icon={<TestTube className="h-12 w-12" />}
            title="No tests found"
            description={searchQuery ? "Try adjusting your search terms" : "No test templates available"}
          />
        ) : (
          filteredTemplates.map((template) => (
            <Card key={template.id} className="overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-center space-x-3">
                  {template.icon}
                  <div className="flex-1">
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription className="text-sm">{template.description}</CardDescription>
                  </div>
                  <Badge variant="outline" className="text-xs">{template.category}</Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  {template.tests.map((test) => (
                    <div key={test.id} className="flex items-start space-x-3 p-2 rounded-md hover:bg-muted/50 transition-colors">
                      <Checkbox
                        checked={isTestSelected(test.id)}
                        onCheckedChange={() => toggleTestSelection(test.id)}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm leading-tight">{test.name}</h4>
                        <p className="text-xs text-muted-foreground mt-1">{test.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))
        )}

        {/* Show existing suites if available */}
        {suites?.suites && suites.suites.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <FolderOpen className="h-4 w-4" />
                <CardTitle className="text-base">Existing Suites</CardTitle>
              </div>
              <CardDescription>Load tests from saved suites</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {suites.suites.slice(0, 3).map((suite: any) => (
                  <div key={suite.id} className="flex items-center justify-between p-2 border rounded-md">
                    <div>
                      <p className="font-medium text-sm">{suite.name}</p>
                      <p className="text-xs text-muted-foreground">{suite.tests?.length || 0} tests</p>
                    </div>
                    <Button variant="ghost" size="sm">Load</Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        </div>
      </ScrollArea>
    </div>
  )
}
