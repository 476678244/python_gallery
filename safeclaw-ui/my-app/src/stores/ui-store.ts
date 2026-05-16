/**
 * UI Store - Pure UI State Management
 * Handles layout, sidebar, theme, modals - no business logic
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SidebarView = "sessions" | "skills" | "memory" | "safety" | "system" | "settings";
export type RightPanelKey = "exec" | "skills" | "budget" | "log" | "shell" | "context" | "memory";
export type Theme = "light" | "dark" | "system";

interface UIState {
  // Sidebar state
  sidebarOpen: boolean;
  sidebarView: SidebarView;
  sidebarWidth: number;

  // Right panel accordion state
  // Ordered list of open panel keys; collapsed keys have a "!" prefix
  openPanelKeys: string[];
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

  // Right panel accordion actions
  railToggle: (key: RightPanelKey) => void;
  collapseToggle: (key: RightPanelKey) => void;
  closeAllPanels: () => void;
  isPanelOpen: (key: RightPanelKey) => boolean;
  isPanelExpanded: (key: RightPanelKey) => boolean;
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

  openPanelKeys: [],
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

      // Right panel accordion
      isPanelOpen: (key) => {
        const keys = get().openPanelKeys;
        return keys.includes(key) || keys.includes("!" + key);
      },
      isPanelExpanded: (key) => get().openPanelKeys.includes(key),

      railToggle: (key) => {
        const keys = get().openPanelKeys;
        if (keys.includes(key)) {
          // collapse it
          set({ openPanelKeys: keys.map((k) => (k === key ? "!" + key : k)) });
        } else if (keys.includes("!" + key)) {
          // expand it
          set({ openPanelKeys: keys.map((k) => (k === "!" + key ? key : k)) });
        } else {
          // add new (expanded)
          set({ openPanelKeys: [...keys, key] });
        }
      },

      collapseToggle: (key) => {
        const keys = get().openPanelKeys;
        if (keys.includes(key)) {
          set({ openPanelKeys: keys.map((k) => (k === key ? "!" + key : k)) });
        } else if (keys.includes("!" + key)) {
          set({ openPanelKeys: keys.map((k) => (k === "!" + key ? key : k)) });
        }
      },

      closeAllPanels: () => set({ openPanelKeys: [] }),
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
        openPanelKeys: state.openPanelKeys,
        rightPanelWidth: state.rightPanelWidth,
        theme: state.theme,
      }),
    }
  )
);
