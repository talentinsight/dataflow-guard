import { useTestSelectionStore } from '@/lib/stores/testSelectionStore'
import { act, renderHook } from '@testing-library/react'

describe('TestSelectionStore', () => {
  beforeEach(() => {
    // Reset store before each test
    const { result } = renderHook(() => useTestSelectionStore())
    act(() => {
      result.current.clearSelection()
    })
  })

  it('should initialize with empty selection', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    
    expect(result.current.selectedTestIds.size).toBe(0)
    expect(result.current.getSelectedCount()).toBe(0)
  })

  it('should toggle test selection correctly', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    const testId = 'test-1'

    // Initially not selected
    expect(result.current.isSelected(testId)).toBe(false)

    // Toggle to select
    act(() => {
      result.current.toggleTestSelection(testId)
    })
    expect(result.current.isSelected(testId)).toBe(true)
    expect(result.current.getSelectedCount()).toBe(1)

    // Toggle to deselect
    act(() => {
      result.current.toggleTestSelection(testId)
    })
    expect(result.current.isSelected(testId)).toBe(false)
    expect(result.current.getSelectedCount()).toBe(0)
  })

  it('should select multiple tests', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    const testIds = ['test-1', 'test-2', 'test-3']

    testIds.forEach(testId => {
      act(() => {
        result.current.selectTest(testId)
      })
    })

    expect(result.current.getSelectedCount()).toBe(3)
    testIds.forEach(testId => {
      expect(result.current.isSelected(testId)).toBe(true)
    })
  })

  it('should deselect specific test', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    const testIds = ['test-1', 'test-2', 'test-3']

    // Select all tests
    testIds.forEach(testId => {
      act(() => {
        result.current.selectTest(testId)
      })
    })

    // Deselect one test
    act(() => {
      result.current.deselectTest('test-2')
    })

    expect(result.current.getSelectedCount()).toBe(2)
    expect(result.current.isSelected('test-1')).toBe(true)
    expect(result.current.isSelected('test-2')).toBe(false)
    expect(result.current.isSelected('test-3')).toBe(true)
  })

  it('should clear all selections', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    const testIds = ['test-1', 'test-2', 'test-3']

    // Select all tests
    testIds.forEach(testId => {
      act(() => {
        result.current.selectTest(testId)
      })
    })

    expect(result.current.getSelectedCount()).toBe(3)

    // Clear all
    act(() => {
      result.current.clearSelection()
    })

    expect(result.current.getSelectedCount()).toBe(0)
    testIds.forEach(testId => {
      expect(result.current.isSelected(testId)).toBe(false)
    })
  })

  it('should select all from array', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    const testIds = ['test-1', 'test-2', 'test-3']

    act(() => {
      result.current.selectAll(testIds)
    })

    expect(result.current.getSelectedCount()).toBe(3)
    testIds.forEach(testId => {
      expect(result.current.isSelected(testId)).toBe(true)
    })
  })

  it('should handle duplicate selections gracefully', () => {
    const { result } = renderHook(() => useTestSelectionStore())
    const testId = 'test-1'

    // Select same test multiple times
    act(() => {
      result.current.selectTest(testId)
      result.current.selectTest(testId)
      result.current.selectTest(testId)
    })

    expect(result.current.getSelectedCount()).toBe(1)
    expect(result.current.isSelected(testId)).toBe(true)
  })
})
