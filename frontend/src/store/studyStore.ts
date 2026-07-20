import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createEmptyStudyDraft, type StudyDraft, type WizardStepId } from '../types/study';

interface StudyStoreState {
  studies: Record<string, StudyDraft>;
  createStudy: (name: string) => string;
  updateStudy: (id: string, patch: Partial<StudyDraft>) => void;
  markStepComplete: (id: string, step: WizardStepId) => void;
  getStudy: (id: string) => StudyDraft | undefined;
  findByBackendId: (backendId: number) => StudyDraft | undefined;
  /** Records a successful backend sync WITHOUT bumping `updatedAt` — unlike
   * updateStudy, this must not itself mark the draft dirty again, or every
   * autosave would immediately re-trigger another autosave. */
  markSynced: (id: string, syncedAt: string) => void;
  /** Same "don't bump updatedAt" rule as markSynced, for patches that only
   * echo back backend-assigned ids (e.g. equipment line ids after a sync) —
   * writing them via updateStudy would retrigger the autosave debounce
   * forever, since it watches updatedAt (GC-COOLING-11). */
  patchSilently: (id: string, patch: Partial<StudyDraft>) => void;
}

export const useStudyStore = create<StudyStoreState>()(
  persist(
    (set, get) => ({
      studies: {},
      createStudy: (name: string) => {
        const id = crypto.randomUUID();
        const draft = createEmptyStudyDraft(id, name);
        set((state) => ({ studies: { ...state.studies, [id]: draft } }));
        return id;
      },
      updateStudy: (id, patch) => {
        set((state) => {
          const existing = state.studies[id];
          if (!existing) return state;
          return {
            studies: {
              ...state.studies,
              [id]: { ...existing, ...patch, updatedAt: new Date().toISOString() },
            },
          };
        });
      },
      markStepComplete: (id, step) => {
        set((state) => {
          const existing = state.studies[id];
          if (!existing) return state;
          const completedSteps = existing.completedSteps.includes(step)
            ? existing.completedSteps
            : [...existing.completedSteps, step];
          return { studies: { ...state.studies, [id]: { ...existing, completedSteps } } };
        });
      },
      getStudy: (id) => get().studies[id],
      findByBackendId: (backendId) => Object.values(get().studies).find((s) => s.backendId === backendId),
      markSynced: (id, syncedAt) => {
        set((state) => {
          const existing = state.studies[id];
          if (!existing) return state;
          return { studies: { ...state.studies, [id]: { ...existing, lastSyncedAt: syncedAt } } };
        });
      },
      patchSilently: (id, patch) => {
        set((state) => {
          const existing = state.studies[id];
          if (!existing) return state;
          return { studies: { ...state.studies, [id]: { ...existing, ...patch } } };
        });
      },
    }),
    { name: 'gc-cooling-studies' },
  ),
);

interface UiState {
  helpOpen: boolean;
  toggleHelp: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  helpOpen: false,
  toggleHelp: () => set((state) => ({ helpOpen: !state.helpOpen })),
}));

/**
 * Transient (non-persisted) autosave status per study id. Deliberately
 * separate from studyStore: "currently saving" or "last save failed" are
 * facts about this browser tab's in-flight request, not durable draft
 * content — persisting them would show a stale "Erreur" banner after a
 * reload even though nothing is actually wrong anymore.
 */
interface SyncStatusState {
  saving: Record<string, boolean>;
  errors: Record<string, string | null>;
  setSaving: (id: string, saving: boolean) => void;
  setError: (id: string, message: string | null) => void;
}

export const useSyncStatusStore = create<SyncStatusState>((set) => ({
  saving: {},
  errors: {},
  setSaving: (id, saving) => set((state) => ({ saving: { ...state.saving, [id]: saving } })),
  setError: (id, message) => set((state) => ({ errors: { ...state.errors, [id]: message } })),
}));
