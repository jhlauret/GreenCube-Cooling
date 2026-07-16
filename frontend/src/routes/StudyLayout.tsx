import { Navigate, Outlet, useParams } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Stepper } from '../components/layout/Stepper';
import { useStudyStore } from '../store/studyStore';
import { WIZARD_STEPS, type WizardStepId } from '../types/study';

export function StudyLayout() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
  }

  const path = window.location.pathname.split('/').pop();
  const currentStep = (WIZARD_STEPS.find((s) => s.path === path)?.id ?? 'location') as WizardStepId;

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader />
      <Stepper studyId={studyId} currentStep={currentStep} completedSteps={study.completedSteps} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-6">
        <Outlet context={{ study }} />
      </main>
    </div>
  );
}
