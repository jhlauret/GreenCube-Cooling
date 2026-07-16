import { useNavigate, useParams } from 'react-router-dom';
import { useStudyStore } from '../store/studyStore';
import { WIZARD_STEPS, type WizardStepId } from '../types/study';

export function useWizardNav(currentStep: WizardStepId) {
  const { studyId } = useParams<{ studyId: string }>();
  const navigate = useNavigate();
  const markStepComplete = useStudyStore((state) => state.markStepComplete);

  const index = WIZARD_STEPS.findIndex((s) => s.id === currentStep);
  const prevStep = WIZARD_STEPS[index - 1];
  const nextStep = WIZARD_STEPS[index + 1];

  function goToPrevious() {
    if (!studyId || !prevStep) return;
    navigate(`/cooling/studies/${studyId}/${prevStep.path}`);
  }

  function goToNext() {
    if (!studyId) return;
    markStepComplete(studyId, currentStep);
    if (nextStep) {
      navigate(`/cooling/studies/${studyId}/${nextStep.path}`);
    } else {
      navigate(`/cooling/studies/${studyId}/results`);
    }
  }

  return { studyId: studyId as string, goToPrevious, goToNext, hasPrevious: !!prevStep };
}
