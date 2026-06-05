/**
 * UI Store - Pure UI State Management
 * Handles layout, sidebar, theme, modals - no business logic
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SidebarView = "sessions" | "skills" | "memory" | "safety" | "system" | "settings";
export type RightPanelKey = "exec" | "skills" | "budget" | "log" | "shell" | "prompts" | "memory";
export type Theme = "light" | "dark" | "system";

// Panel heights in pixels (min: 60, max: 600)
const DEFAULT_PANEL_HEIGHT = 200;
const MIN_PANEL_HEIGHT = 60;
const MAX_PANEL_HEIGHT = 600;

interface UIState {
  // Sidebar state
  sidebarOpen: boolean;
  sidebarView: SidebarView;
  sidebarWidth: number;

  // Right panel accordion state
  // Ordered list of open panel keys; collapsed keys have a "!" prefix
  openPanelKeys: string[];
  rightPanelWidth: number;
  // Panel heights (key -> height in px)
  panelHeights: Record<RightPanelKey, number>;

  // LLM Call navigation - synced across exec/skills/prompts panels
  currentCallIndex: number;
  totalCalls: number;

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
  getPanelHeight: (key: RightPanelKey) => number;
  setPanelHeight: (key: RightPanelKey, height: number) => void;

  // LLM Call navigation actions
  setCurrentCallIndex: (index: number) => void;
  nextCall: () => void;
  prevCall: () => void;
  setTotalCalls: (total: number) => void;

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
  panelHeights: {
    exec: DEFAULT_PANEL_HEIGHT,
    skills: DEFAULT_PANEL_HEIGHT,
    budget: DEFAULT_PANEL_HEIGHT,
    log: DEFAULT_PANEL_HEIGHT,
    shell: DEFAULT_PANEL_HEIGHT,
    prompts: DEFAULT_PANEL_HEIGHT,
    memory: DEFAULT_PANEL_HEIGHT,
  },

  // LLM Call navigation - start at 0, will be updated by panels
  currentCallIndex: 0,
  totalCalls: 0,

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
        if (keys.includes(key) || keys.includes("!" + key)) {
          // Panel is already open (expanded or collapsed) → close it
          set({ openPanelKeys: keys.filter((k) => k !== key && k !== "!" + key) });
        } else {
          // Panel is closed → open it (expanded by default)
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
      setRightPanelWidth: (width) => set({ rightPanelWidth: Math.max(200, Math.min(600, width)) }),

      getPanelHeight: (key) => {
        const h = get().panelHeights[key];
        return h ?? DEFAULT_PANEL_HEIGHT;
      },
      setPanelHeight: (key, height) => {
        set({
          panelHeights: {
            ...get().panelHeights,
            [key]: Math.max(MIN_PANEL_HEIGHT, Math.min(MAX_PANEL_HEIGHT, height)),
          },
        });
      },

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

      // LLM Call navigation
      setCurrentCallIndex: (index) => {
        const total = get().totalCalls;
        set({
          currentCallIndex: Math.max(0, Math.min(total - 1, index))
        });
      },
      nextCall: () => {
        const { currentCallIndex, totalCalls } = get();
        if (currentCallIndex < totalCalls - 1) {
          set({ currentCallIndex: currentCallIndex + 1 });
        }
      },
      prevCall: () => {
        const { currentCallIndex } = get();
        if (currentCallIndex > 0) {
          set({ currentCallIndex: currentCallIndex - 1 });
        }
      },
      setTotalCalls: (total) => set({ totalCalls: total }),
    }),
    {
      name: "safeclaw-ui-store",
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        sidebarWidth: state.sidebarWidth,
        openPanelKeys: state.openPanelKeys,
        rightPanelWidth: state.rightPanelWidth,
        panelHeights: state.panelHeights,
        theme: state.theme,
      }),
    }
  )
);
