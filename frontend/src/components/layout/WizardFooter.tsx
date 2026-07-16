import type { ReactNode } from 'react';
import { Button } from '../ui/Button';

interface NextStep {
  icon: ReactNode;
  label: string;
}

interface WizardFooterProps {
  nextSteps: NextStep[];
  onBack?: () => void;
  onContinue: () => void;
  continueLabel?: string;
  continueDisabled?: boolean;
}

export function WizardFooter({ nextSteps, onBack, onContinue, continueLabel = 'Continuer →', continueDisabled }: WizardFooterProps) {
  return (
    <div className="flex flex-col gap-4 border-t border-border bg-surface px-8 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-6">
        <span className="text-sm font-medium text-ink">Ce que nous allons faire ensuite</span>
        <div className="flex flex-wrap gap-6">
          {nextSteps.map((step, index) => (
            <div key={step.label} className="flex items-center gap-2 text-sm text-ink-soft">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                {step.icon}
              </span>
              <span>
                {index + 1}. {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {onBack && (
          <Button variant="secondary" onClick={onBack}>
            ← Retour
          </Button>
        )}
        <Button onClick={onContinue} disabled={continueDisabled}>
          {continueLabel}
        </Button>
      </div>
    </div>
  );
}
