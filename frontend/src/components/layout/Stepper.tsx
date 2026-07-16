import clsx from 'clsx';
import { WIZARD_STEPS, type WizardStepId } from '../../types/study';
import { Link } from 'react-router-dom';

interface StepperProps {
  studyId: string;
  currentStep: WizardStepId;
  completedSteps: WizardStepId[];
}

export function Stepper({ studyId, currentStep, completedSteps }: StepperProps) {
  return (
    <nav
      aria-label="Étapes de la configuration"
      className="flex items-center overflow-x-auto border-b border-border bg-surface px-8 py-4"
    >
      {WIZARD_STEPS.map((step, index) => {
        const isCompleted = completedSteps.includes(step.id);
        const isCurrent = step.id === currentStep;
        const isReachable = isCompleted || isCurrent || index === 0;

        return (
          <div key={step.id} className="flex items-center">
            {isReachable ? (
              <Link
                to={`/cooling/studies/${studyId}/${step.path}`}
                className="flex items-center gap-2 whitespace-nowrap"
                aria-current={isCurrent ? 'step' : undefined}
              >
                <StepBadge order={step.order} isCompleted={isCompleted} isCurrent={isCurrent} />
                <span className={clsx('text-sm', isCurrent ? 'font-semibold text-ink' : 'text-ink-soft')}>
                  {step.label}
                </span>
              </Link>
            ) : (
              <div className="flex items-center gap-2 whitespace-nowrap opacity-50">
                <StepBadge order={step.order} isCompleted={isCompleted} isCurrent={isCurrent} />
                <span className="text-sm text-ink-soft">{step.label}</span>
              </div>
            )}
            {index < WIZARD_STEPS.length - 1 && (
              <div
                className={clsx(
                  'mx-3 h-px w-8 shrink-0',
                  isCompleted ? 'bg-brand-400' : 'bg-border',
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}

function StepBadge({ order, isCompleted, isCurrent }: { order: number; isCompleted: boolean; isCurrent: boolean }) {
  return (
    <span
      className={clsx(
        'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold',
        isCompleted && !isCurrent && 'border-brand-500 bg-brand-50 text-brand-600',
        isCurrent && 'border-brand-600 bg-brand-600 text-white',
        !isCompleted && !isCurrent && 'border-border bg-surface text-ink-faint',
      )}
    >
      {isCompleted && !isCurrent ? '✓' : order}
    </span>
  );
}
