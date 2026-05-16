/**
 * UI Store - Pure UI State Management
 * Handles layout, sidebar, theme, modals - no business logic
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SidebarView = "sessions" | "skills" | "memory" | "safety" | "system" | "settings";
export type RightPanelView = "execution" | "skills" | "context" | "none";
export type Theme = "light" | "dark" | "system";

interface UIState {
  // Sidebar state
  sidebarOpen: boolean;
  sidebarView: SidebarView;
  sidebarWidth: number;

  // Right panel state
  rightPanelOpen: boolean;
  rightPanelView: RightPanelView;
  rightPanelWidth: number;

  // Theme
  theme: Theme;

  // Modals
  activeModal: string | null;
  modalData: Record<string, unknown> | null;

  // Global UI flags
  isFullscreen: boolean;
  showKeyboardShortcuts: boolean;
}

interface UIActions {
  // Sidebar actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarView: (view: SidebarView) => void;
  setSidebarWidth: (width: number) => void;

  // Right panel actions
  toggleRightPanel: () => void;
  setRightPanelOpen: (open: boolean) => void;
  setRightPanelView: (view: RightPanelView) => void;
  setRightPanelWidth: (width: number) => void;

  // Theme actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;

  // Modal actions
  openModal: (modalId: string, data?: Record<string, unknown>) => void;
  closeModal: () => void;

  // Fullscreen
  toggleFullscreen: () => void;

  // Keyboard shortcuts
  toggleKeyboardShortcuts: () => void;
}

const initialUIState: UIState = {
  sidebarOpen: true,
  sidebarView: "sessions",
  sidebarWidth: 256,

  rightPanelOpen: true,
  rightPanelView: "execution",
  rightPanelWidth: 320,

  theme: "system",

  activeModal: null,
  modalData: null,

  isFullscreen: false,
  showKeyboardShortcuts: false,
};

export const useUIStore = create<UIState & UIActions>()(
  persist(
    (set, get) => ({
      ...initialUIState,

      // Sidebar
      toggleSidebar: () => set({ sidebarOpen: !get().sidebarOpen }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarView: (view) => set({ sidebarView: view }),
      setSidebarWidth: (width) => set({ sidebarWidth: width }),

      // Right panel
      toggleRightPanel: () => set({ rightPanelOpen: !get().rightPanelOpen }),
      setRightPanelOpen: (open) => set({ rightPanelOpen: open }),
      setRightPanelView: (view) => set({ rightPanelView: view }),
      setRightPanelWidth: (width) => set({ rightPanelWidth: width }),

      // Theme
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => {
        const themes: Theme[] = ["light", "dark", "system"];
        const currentIndex = themes.indexOf(get().theme);
        const nextTheme = themes[(currentIndex + 1) % themes.length];
        set({ theme: nextTheme });
      },

      // Modals
      openModal: (modalId, data) => set({ activeModal: modalId, modalData: data || null }),
      closeModal: () => set({ activeModal: null, modalData: null }),

      // Fullscreen
      toggleFullscreen: () => set({ isFullscreen: !get().isFullscreen }),

      // Keyboard shortcuts
      toggleKeyboardShortcuts: () =>
        set({ showKeyboardShortcuts: !get().showKeyboardShortcuts }),
    }),
    {
      name: "safeclaw-ui-store",
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        sidebarWidth: state.sidebarWidth,
        rightPanelOpen: state.rightPanelOpen,
        rightPanelWidth: state.rightPanelWidth,
        theme: state.theme,
      }),
    }
  )
);
