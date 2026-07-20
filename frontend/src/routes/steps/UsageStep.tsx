import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { SelectableCard } from '../../components/ui/SelectableCard';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { StudyDraft, UsageType } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';

const USAGE_TYPES: { code: UsageType; label: string; icon: string }[] = [
  { code: 'office', label: 'Bureau', icon: '💼' },
  { code: 'residential', label: 'Logement', icon: '🏠' },
  { code: 'meeting_room', label: 'Salle de réunion', icon: '👥' },
  { code: 'commerce', label: 'Commerce', icon: '🛍️' },
  { code: 'workshop', label: 'Atelier', icon: '🔧' },
  { code: 'medical', label: 'Cabinet médical', icon: '🩺' },
  { code: 'server_room', label: 'Salle informatique', icon: '🖥️' },
  { code: 'other', label: 'Autre', icon: '⋯' },
];

export function UsageStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('usage');
  const { usage } = study;

  const sensibleW = usage.usualOccupants * 70;
  const latentGH = usage.usualOccupants * 50;
  const totalKw = (sensibleW + latentGH * 0.68) / 1000;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <Card title="Comment le GreenCube sera-t-il utilisé ?">
            <div className="grid grid-cols-4 gap-3">
              {USAGE_TYPES.map((u) => (
                <SelectableCard
                  key={u.code}
                  selected={usage.usageType === u.code}
                  onClick={() => updateStudy(studyId, { usage: { ...usage, usageType: u.code } })}
                  icon={u.icon}
                  label={u.label}
                />
              ))}
            </div>
          </Card>

          <Card title="Occupation et planning d'utilisation">
            <div className="grid grid-cols-2 gap-4">
              <LabeledNumber
                label="Nombre habituel d'occupants"
                value={usage.usualOccupants}
                min={0}
                max={200}
                onChange={(v) => updateStudy(studyId, { usage: { ...usage, usualOccupants: v } })}
              />
              <LabeledNumber
                label="Nombre maximal d'occupants"
                value={usage.maximumOccupants}
                min={usage.usualOccupants}
                max={200}
                onChange={(v) => updateStudy(studyId, { usage: { ...usage, maximumOccupants: v } })}
              />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <LabeledNumber
                label="Heure de début d'occupation"
                value={usage.occupancyStartHour}
                min={0}
                max={23}
                onChange={(v) => updateStudy(studyId, { usage: { ...usage, occupancyStartHour: v } })}
              />
              <LabeledNumber
                label="Heure de fin d'occupation"
                value={usage.occupancyEndHour}
                min={0}
                max={23}
                onChange={(v) => updateStudy(studyId, { usage: { ...usage, occupancyEndHour: v } })}
              />
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <Card title="Profil d'usage">
            <div className="grid grid-cols-3 gap-3">
              <StatTile icon="🏢" label="Type d'usage" value={USAGE_TYPES.find((u) => u.code === usage.usageType)?.label ?? '—'} />
              <StatTile icon="👥" label="Occupation maximale" value={`${usage.maximumOccupants} personnes`} />
              <StatTile icon="🕐" label="Plage horaire" value={`${usage.occupancyStartHour}h - ${usage.occupancyEndHour}h`} />
            </div>
          </Card>

          <Card title="Apports humains estimés">
            <div className="grid grid-cols-3 gap-3">
              <StatTile icon="👥" label="Apport sensible" value={`≈ ${sensibleW.toFixed(0)} W`} valueClassName="text-brand-700" />
              <StatTile icon="💧" label="Apport latent" value={`≈ ${latentGH.toFixed(0)} g/h`} valueClassName="text-brand-700" />
              <StatTile icon="🌿" label="Apport total" value={`≈ ${totalKw.toFixed(1)} kW`} valueClassName="text-brand-700" />
            </div>
          </Card>
        </div>
      </div>

      <WizardFooter nextSteps={defaultNextSteps} onBack={goToPrevious} onContinue={goToNext} />
    </div>
  );
}

function LabeledNumber({
  label,
  value,
  onChange,
  min = 0,
  max = 9999,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-soft">
      {label}
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => {
          const raw = Number(e.target.value);
          if (Number.isFinite(raw)) onChange(Math.min(max, Math.max(min, raw)));
        }}
        className="rounded-lg border border-border px-3 py-2 text-sm text-ink outline-none focus:border-brand-500"
      />
    </label>
  );
}
