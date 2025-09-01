'use client'

import { useState } from 'react'
import Link from 'next/link'
import { StatusChip } from '@/components/common/StatusChip'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PlanPanel } from '@/components/panels/PlanPanel'
import { EditorPanel } from '@/components/panels/EditorPanel'
import { DatasetPanel } from '@/components/panels/DatasetPanel'
import { RunConsole } from '@/components/panels/RunConsole'
import { ResultsPanel } from '@/components/panels/ResultsPanel'
import { Button } from '@/components/ui/button'
import { TestTube, ChevronUp, ChevronDown } from 'lucide-react'

export default function WorkbenchPage() {
  const [showResults, setShowResults] = useState(false)

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <Link href="/workbench" className="mr-6 flex items-center space-x-2">
              <TestTube className="h-6 w-6" />
              <span className="font-bold">DataFlowGuard</span>
            </Link>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <span className="text-foreground">Workbench</span>
              {process.env.NEXT_PUBLIC_SHOW_LEGACY_NAV !== 'false' && (
                <>
                  <Link href="/runs" className="text-foreground/60 transition-colors hover:text-foreground/80">
                    Runs
                  </Link>
                  <Link href="/datasets" className="text-foreground/60 transition-colors hover:text-foreground/80">
                    Datasets
                  </Link>
                  <Link href="/settings" className="text-foreground/60 transition-colors hover:text-foreground/80">
                    Settings
                  </Link>
                </>
              )}
            </nav>
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <StatusChip />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Test Planning */}
        <div className="w-80 border-r bg-muted/30">
          <ErrorBoundary>
            <PlanPanel />
          </ErrorBoundary>
        </div>

        {/* Center Panels - Editor and Dataset */}
        <div className="flex-1 flex flex-col">
          {/* Top Half - Editor */}
          <div className="flex-1 border-b">
            <ErrorBoundary>
              <EditorPanel />
            </ErrorBoundary>
          </div>

          {/* Bottom Half - Dataset */}
          <div className="h-80">
            <ErrorBoundary>
              <DatasetPanel />
            </ErrorBoundary>
          </div>
        </div>

        {/* Right Panel - Run Console */}
        <div className="w-80 border-l">
          <ErrorBoundary>
            <RunConsole />
          </ErrorBoundary>
        </div>
      </div>

      {/* Bottom Drawer - Results Panel */}
      <div className={`border-t transition-all duration-300 ${showResults ? 'h-80' : 'h-12'}`}>
        <div className="h-full flex flex-col">
          {/* Results Header */}
          <div className="h-12 flex items-center justify-between px-4 bg-muted/30">
            <div className="flex items-center space-x-2">
              <span className="font-medium text-sm">Test Results</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowResults(!showResults)}
            >
              {showResults ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronUp className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Results Content */}
          {showResults && (
            <div className="flex-1 overflow-hidden">
              <ErrorBoundary>
                <ResultsPanel />
              </ErrorBoundary>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
