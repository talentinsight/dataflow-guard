import { renderHook, act } from '@testing-library/react'
import { useWorkspaceStore } from '@/stores/workspace'

describe('Test Selection Toggle', () => {
  beforeEach(() => {
    // Reset store before each test
    const { result } = renderHook(() => useWorkspaceStore())
    act(() => {
      result.current.resetWorkspace()
    })
  })

  it('should toggle test selection correctly', () => {
    const { result } = renderHook(() => useWorkspaceStore())
    const testId = 'test-1'

    // Initially not selected
    expect(result.current.isTestSelected(testId)).toBe(false)
    expect(result.current.getSelectedTestCount()).toBe(0)

    // Toggle to select (uncheck → check)
    act(() => {
      result.current.toggleTestSelection(testId)
    })
    expect(result.current.isTestSelected(testId)).toBe(true)
    expect(result.current.getSelectedTestCount()).toBe(1)

    // Toggle to deselect (check → uncheck)
    act(() => {
      result.current.toggleTestSelection(testId)
    })
    expect(result.current.isTestSelected(testId)).toBe(false)
    expect(result.current.getSelectedTestCount()).toBe(0)
  })

  it('should handle multiple test selections', () => {
    const { result } = renderHook(() => useWorkspaceStore())
    const testIds = ['test-1', 'test-2', 'test-3']

    // Select all tests
    testIds.forEach(testId => {
      act(() => {
        result.current.toggleTestSelection(testId)
      })
    })

    expect(result.current.getSelectedTestCount()).toBe(3)
    testIds.forEach(testId => {
      expect(result.current.isTestSelected(testId)).toBe(true)
    })

    // Deselect one test
    act(() => {
      result.current.toggleTestSelection('test-2')
    })

    expect(result.current.getSelectedTestCount()).toBe(2)
    expect(result.current.isTestSelected('test-1')).toBe(true)
    expect(result.current.isTestSelected('test-2')).toBe(false)
    expect(result.current.isTestSelected('test-3')).toBe(true)
  })
})
