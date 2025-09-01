'use client'

// DEPRECATED: This page has been migrated to the unified Workbench
// Run management is now integrated into the workbench interface

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function RunsPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to workbench - run functionality is now integrated
    router.replace('/workbench')
  }, [router])

  return null
}