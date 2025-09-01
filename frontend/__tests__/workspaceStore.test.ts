import { renderHook, act } from '@testing-library/react'
import { useWorkspaceStore } from '@/stores/workspace'

// Reset store before each test
beforeEach(() => {
  useWorkspaceStore.getState().resetWorkspace()
})

describe('useWorkspaceStore', () => {
  describe('test selection', () => {
    it('should toggle test selection correctly', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      // Initially no tests selected
      expect(result.current.getSelectedTestCount()).toBe(0)
      expect(result.current.isTestSelected('test-1')).toBe(false)

      // Select a test
      act(() => {
        result.current.toggleTestSelection('test-1')
      })

      expect(result.current.getSelectedTestCount()).toBe(1)
      expect(result.current.isTestSelected('test-1')).toBe(true)

      // Toggle same test again should deselect it
      act(() => {
        result.current.toggleTestSelection('test-1')
      })

      expect(result.current.getSelectedTestCount()).toBe(0)
      expect(result.current.isTestSelected('test-1')).toBe(false)
    })

    it('should handle multiple test selections', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      // Select multiple tests
      act(() => {
        result.current.toggleTestSelection('test-1')
        result.current.toggleTestSelection('test-2')
        result.current.toggleTestSelection('test-3')
      })

      expect(result.current.getSelectedTestCount()).toBe(3)
      expect(result.current.isTestSelected('test-1')).toBe(true)
      expect(result.current.isTestSelected('test-2')).toBe(true)
      expect(result.current.isTestSelected('test-3')).toBe(true)

      // Deselect one test
      act(() => {
        result.current.toggleTestSelection('test-2')
      })

      expect(result.current.getSelectedTestCount()).toBe(2)
      expect(result.current.isTestSelected('test-1')).toBe(true)
      expect(result.current.isTestSelected('test-2')).toBe(false)
      expect(result.current.isTestSelected('test-3')).toBe(true)
    })

    it('should clear all test selections', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      // Select multiple tests
      act(() => {
        result.current.toggleTestSelection('test-1')
        result.current.toggleTestSelection('test-2')
        result.current.toggleTestSelection('test-3')
      })

      expect(result.current.getSelectedTestCount()).toBe(3)

      // Clear all selections
      act(() => {
        result.current.clearTestSelection()
      })

      expect(result.current.getSelectedTestCount()).toBe(0)
      expect(result.current.isTestSelected('test-1')).toBe(false)
      expect(result.current.isTestSelected('test-2')).toBe(false)
      expect(result.current.isTestSelected('test-3')).toBe(false)
    })
  })

  describe('workspace state management', () => {
    it('should manage builder text', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      expect(result.current.builderText).toBe('')

      act(() => {
        result.current.setBuilderText('SELECT * FROM test_table')
      })

      expect(result.current.builderText).toBe('SELECT * FROM test_table')
    })

    it('should manage run state', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      expect(result.current.runId).toBe(null)
      expect(result.current.status).toBe('idle')

      act(() => {
        result.current.setRunId('run-123')
        result.current.setStatus('running')
      })

      expect(result.current.runId).toBe('run-123')
      expect(result.current.status).toBe('running')
    })

    it('should manage dataset metadata', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      expect(result.current.datasetMeta).toBe(null)

      const mockDataset = {
        name: 'test.csv',
        columns: [{ name: 'id', type: 'number' }],
        rows: [{ id: 1 }],
        totalRows: 1
      }

      act(() => {
        result.current.setDatasetMeta(mockDataset)
      })

      expect(result.current.datasetMeta).toEqual(mockDataset)
    })

    it('should reset workspace completely', () => {
      const { result } = renderHook(() => useWorkspaceStore())

      // Set up some state
      act(() => {
        result.current.toggleTestSelection('test-1')
        result.current.setBuilderText('SELECT * FROM test')
        result.current.setRunId('run-123')
        result.current.setStatus('running')
        result.current.setDatasetMeta({
          name: 'test.csv',
          columns: [],
          rows: [],
          totalRows: 0
        })
      })

      // Verify state is set
      expect(result.current.getSelectedTestCount()).toBe(1)
      expect(result.current.builderText).toBe('SELECT * FROM test')
      expect(result.current.runId).toBe('run-123')
      expect(result.current.status).toBe('running')
      expect(result.current.datasetMeta).not.toBe(null)

      // Reset workspace
      act(() => {
        result.current.resetWorkspace()
      })

      // Verify everything is reset
      expect(result.current.getSelectedTestCount()).toBe(0)
      expect(result.current.builderText).toBe('')
      expect(result.current.runId).toBe(null)
      expect(result.current.status).toBe('idle')
      expect(result.current.datasetMeta).toBe(null)
    })
  })
})
