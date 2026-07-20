import { Navigate, Outlet, useParams } from 'react-router-dom';
import { AppHeader, type SyncState } from '../components/layout/AppHeader';
import { Stepper } from '../components/layout/Stepper';
import { useStudyStore, useSyncStatusStore } from '../store/studyStore';
import { WIZARD_STEPS, type StudyDraft, type WizardStepId } from '../types/study';
import { useAutosave } from '../sync/useAutosave';

function deriveSyncState(study: StudyDraft, saving: boolean, error: string | null): SyncState {
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

  const path = window.location.pathname.split('/').pop();
  const currentStep = (WIZARD_STEPS.find((s) => s.path === path)?.id ?? 'location') as WizardStepId;

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader syncState={deriveSyncState(study, saving, error)} syncErrorMessage={error} />
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
