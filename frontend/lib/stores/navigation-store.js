import { create } from 'zustand'

export const useNavigationStore = create((set) => ({
  activeComponent: null,
  setActiveComponent: (component) => set({ activeComponent: component }),
}))