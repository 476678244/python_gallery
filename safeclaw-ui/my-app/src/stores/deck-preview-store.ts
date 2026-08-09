/**
 * Deck preview store — PPT Observability pack (docs/features/ppt-mode).
 */

import { create } from "zustand";

export interface DeckPreviewState {
  deckId: string | null;
  version: number | null;
  pptxPath: string | null;
  previewUrls: string[];
  selectedSlide: number; // 1-based
  error: string | null;
  versions: Array<{
    version: number;
    previewUrls: string[];
    pptxPath?: string;
  }>;
}

interface DeckPreviewActions {
  applyPreviewEvent: (ev: {
    deck_id?: string;
    version?: number;
    pptx_path?: string;
    preview_urls?: string[];
    error?: string;
  }) => void;
  selectSlide: (n: number) => void;
  selectVersion: (version: number) => void;
  clear: () => void;
}

const initial: DeckPreviewState = {
  deckId: null,
  version: null,
  pptxPath: null,
  previewUrls: [],
  selectedSlide: 1,
  error: null,
  versions: [],
};

export const useDeckPreviewStore = create<DeckPreviewState & DeckPreviewActions>(
  (set, get) => ({
    ...initial,

    applyPreviewEvent: (ev) => {
      if (ev.error) {
        set({ error: ev.error });
        return;
      }
      const urls = ev.preview_urls || [];
      const version = ev.version ?? null;
      const deckId = ev.deck_id ?? get().deckId;
      const pptxPath = ev.pptx_path ?? null;
      const prev = get().versions.filter((v) => v.version !== version);
      const versions =
        version != null
          ? [...prev, { version, previewUrls: urls, pptxPath: pptxPath || undefined }].sort(
              (a, b) => a.version - b.version
            )
          : get().versions;
      set({
        deckId,
        version,
        pptxPath,
        previewUrls: urls,
        selectedSlide: 1,
        error: null,
        versions,
      });
    },

    selectSlide: (n) => {
      const max = Math.max(1, get().previewUrls.length);
      set({ selectedSlide: Math.max(1, Math.min(max, n)) });
    },

    selectVersion: (version) => {
      const hit = get().versions.find((v) => v.version === version);
      if (!hit) {
        throw new Error(
          `[DeckPreview] Unknown version\n  version: ${version}\n  known: ${get()
            .versions.map((v) => v.version)
            .join(",")}`
        );
      }
      set({
        version: hit.version,
        previewUrls: hit.previewUrls,
        pptxPath: hit.pptxPath ?? get().pptxPath,
        selectedSlide: 1,
      });
    },

    clear: () => set({ ...initial }),
  })
);
