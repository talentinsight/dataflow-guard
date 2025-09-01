'use client'

// DEPRECATED: This page has been migrated to the unified Workbench
// Redirect users to the new workbench interface

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function BuilderPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to workbench - builder functionality is now integrated
    router.replace('/workbench')
  }, [router])

  return null
}