import { create } from "zustand"

interface UIStore {
  isSidebarOpen: boolean
  isInspectorOpen: boolean
  selectedModel: string
  hasPipelineRun: boolean
  isGraphSelectorOpen: boolean
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setInspectorOpen: (open: boolean) => void
  toggleInspector: () => void
  setSelectedModel: (model: string) => void
  setHasPipelineRun: (has: boolean) => void
  setGraphSelectorOpen: (open: boolean) => void
}

export const useUIStore = create<UIStore>((set) => ({
  isSidebarOpen: true,
  isInspectorOpen: true,
  selectedModel: "Gemini 1.5 Flash",
  hasPipelineRun: false,
  isGraphSelectorOpen: false,
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setInspectorOpen: (open) => set({ isInspectorOpen: open }),
  toggleInspector: () => set((state) => ({ isInspectorOpen: !state.isInspectorOpen })),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setHasPipelineRun: (has) => set({ hasPipelineRun: has }),
  setGraphSelectorOpen: (open) => set({ isGraphSelectorOpen: open }),
}))
