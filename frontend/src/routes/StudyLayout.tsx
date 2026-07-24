import { Navigate, Outlet, useParams } from 'react-router-dom';
import { AppHeader, type SyncState } from '../components/layout/AppHeader';
import { Stepper } from '../components/layout/Stepper';
import { useStudyStore, useSyncStatusStore } from '../store/studyStore';
import { WIZARD_STEPS, type StudyDraft, type WizardStepId } from '../types/study';
import { useAutosave } from '../sync/useAutosave';
import { loadStudyFromBackend } from '../sync/syncStudy';

function deriveSyncState(study: StudyDraft, saving: boolean, error: string | null, conflict: boolean): SyncState {
  if (conflict) return 'conflict';
  if (error) return 'error';
  if (saving) return 'saving';
  if (!study.backendId) return 'local';
  const dirty = !study.lastSyncedAt || new Date(study.updatedAt) > new Date(study.lastSyncedAt);
  return dirty ? 'dirty' : 'synced';
}

function StudyLayoutContent({ studyId, study }: { studyId: string; study: StudyDraft }) {
  useAutosave(study);
  const saving = useSyncStatusStore((state) => state.saving[study.id] ?? false);
  const error = useSyncStatusStore((state) => state.errors[study.id] ?? null);
  const conflict = useSyncStatusStore((state) => state.conflicts[study.id] ?? false);
  const setConflict = useSyncStatusStore((state) => state.setConflict);
  const setError = useSyncStatusStore((state) => state.setError);
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const markSynced = useStudyStore((state) => state.markSynced);

  const path = window.location.pathname.split('/').pop();
  const currentStep = (WIZARD_STEPS.find((s) => s.path === path)?.id ?? 'location') as WizardStepId;

  /**
   * "Recharger depuis Odoo": discards the local draft's unsynced edits and
   * replaces it with the backend's current state, then clears the conflict
   * so autosave can resume. This is the explicit reload path required by
   * GC-COOLING-06 §17 — never an automatic silent overwrite in either
   * direction.
   */
  async function handleReload() {
    if (!study.backendId) return;
    const patch = await loadStudyFromBackend(study.backendId);
    updateStudy(study.id, patch);
    markSynced(study.id, new Date().toISOString());
    setConflict(study.id, false);
    setError(study.id, null);
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader
        syncState={deriveSyncState(study, saving, error, conflict)}
        syncErrorMessage={error}
        onReload={conflict ? () => void handleReload() : null}
      />
      <Stepper studyId={studyId} currentStep={currentStep} completedSteps={study.completedSteps} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-6">
        <Outlet context={{ study }} />
      </main>
    </div>
  );
}

export function StudyLayout() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
  }

  return <StudyLayoutContent studyId={studyId} study={study} />;
}
