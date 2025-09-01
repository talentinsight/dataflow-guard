import { create } from 'zustand';

export type WorkspaceStatus = 'idle' | 'running' | 'done' | 'error';

interface DatasetMeta {
  name: string;
  columns: { name: string; type: string }[];
  rows: any[];
  totalRows: number;
}

interface WorkspaceState {
  // Test selection (reusing existing pattern)
  selectedTests: Set<string>;
  
  // Dataset management
  datasetMeta: DatasetMeta | null;
  
  // Editor state
  builderText: string;
  
  // Run management
  runId: string | null;
  status: WorkspaceStatus;
  
  // Actions
  toggleTestSelection: (testId: string) => void;
  clearTestSelection: () => void;
  isTestSelected: (testId: string) => boolean;
  getSelectedTestCount: () => number;
  
  setDatasetMeta: (meta: DatasetMeta | null) => void;
  setBuilderText: (text: string) => void;
  setRunId: (id: string | null) => void;
  setStatus: (status: WorkspaceStatus) => void;
  
  // Reset workspace
  resetWorkspace: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  // Initial state
  selectedTests: new Set<string>(),
  datasetMeta: null,
  builderText: '',
  runId: null,
  status: 'idle',
  
  // Test selection actions (compatible with existing store)
  toggleTestSelection: (testId: string) => {
    set((state) => {
      const newSelectedTests = new Set(state.selectedTests);
      if (newSelectedTests.has(testId)) {
        newSelectedTests.delete(testId);
      } else {
        newSelectedTests.add(testId);
      }
      return { selectedTests: newSelectedTests };
    });
  },
  
  clearTestSelection: () => {
    set({ selectedTests: new Set<string>() });
  },
  
  isTestSelected: (testId: string) => {
    return get().selectedTests.has(testId);
  },
  
  getSelectedTestCount: () => {
    return get().selectedTests.size;
  },
  
  // Dataset actions
  setDatasetMeta: (meta: DatasetMeta | null) => {
    set({ datasetMeta: meta });
  },
  
  // Editor actions
  setBuilderText: (text: string) => {
    set({ builderText: text });
  },
  
  // Run actions
  setRunId: (id: string | null) => {
    set({ runId: id });
  },
  
  setStatus: (status: WorkspaceStatus) => {
    set({ status });
  },
  
  // Reset workspace
  resetWorkspace: () => {
    set({
      selectedTests: new Set<string>(),
      datasetMeta: null,
      builderText: '',
      runId: null,
      status: 'idle',
    });
  },
}));
