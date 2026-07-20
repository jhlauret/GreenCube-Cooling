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
