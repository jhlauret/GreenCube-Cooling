import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { SelectableCard } from '../../components/ui/SelectableCard';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { StudyDraft, UsageType, Weekday } from '../../types/study';
import { WEEKDAYS } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';
import { dailyOccupiedHours } from './usageSchedule';

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

const WEEKDAY_LABELS: Record<Weekday, string> = {
  monday: 'Lun',
  tuesday: 'Mar',
  wednesday: 'Mer',
  thursday: 'Jeu',
  friday: 'Ven',
  saturday: 'Sam',
  sunday: 'Dim',
};

export function UsageStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('usage');
  const { usage } = study;

  const occupiedHours = dailyOccupiedHours(usage.occupancyStartHour, usage.occupancyEndHour);
  const crossesMidnight = usage.occupancyEndHour < usage.occupancyStartHour;
  const occupancyFraction = Math.max(0, Math.min(1, occupiedHours / 24));
  const activeDaysCount = WEEKDAYS.filter((d) => usage.occupiedWeekdays[d]).length;

  // Matches occupancy_profile.py's sensible_gain_per_person_w/
  // latent_gain_per_person_g_h defaults (75 W, 60 g/h) — this preview used
  // to show 70/50, silently diverging from what the backend would actually
  // use to size the study (GC-COOLING-10). It is also now weighted by the
  // same daily occupancy_fraction the backend's MERCURE input builder
  // uses (previously hardcoded to 1.0 server-side, so the schedule below
  // had zero effect on the calculated gains — see cooling_study.py).
  const sensibleW = usage.usualOccupants * occupancyFraction * 75;
  const latentGH = usage.usualOccupants * occupancyFraction * 60;
  const totalKw = (sensibleW + latentGH * 0.68) / 1000;

  const noActiveDay = usage.usualOccupants > 0 && activeDaysCount === 0;

  // Preview only — not presented as a regulatory threshold, matching
  // README §"Densité d'occupation" ("ne pas présenter les seuils comme
  // réglementaires sans source explicite"). The backend recomputes its
  // own view from the study's actual thermal specification floor area.
  const floorAreaM2 = study.model.lengthM * study.model.widthM;
  const densityM2PerPerson = usage.usualOccupants > 0 && floorAreaM2 > 0 ? floorAreaM2 / usage.usualOccupants : null;

  function toggleDay(day: Weekday) {
    updateStudy(studyId, {
      usage: { ...usage, occupiedWeekdays: { ...usage.occupiedWeekdays, [day]: !usage.occupiedWeekdays[day] } },
    });
  }

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
                max={24}
                onChange={(v) => updateStudy(studyId, { usage: { ...usage, occupancyStartHour: v } })}
              />
              <LabeledNumber
                label="Heure de fin d'occupation"
                value={usage.occupancyEndHour}
                min={0}
                max={24}
                onChange={(v) => updateStudy(studyId, { usage: { ...usage, occupancyEndHour: v } })}
              />
            </div>
            {crossesMidnight && (
              <p className="mt-2 text-xs text-ink-soft">
                Ce créneau traverse minuit ({usage.occupancyStartHour}h → {usage.occupancyEndHour}h le lendemain),
                soit {occupiedHours.toFixed(1)} h d'occupation par jour.
              </p>
            )}

            <fieldset className="mt-4">
              <legend className="mb-2 text-xs text-ink-soft">Jours d'occupation</legend>
              <div className="grid grid-cols-7 gap-1">
                {WEEKDAYS.map((day) => (
                  <button
                    key={day}
                    type="button"
                    aria-pressed={usage.occupiedWeekdays[day]}
                    onClick={() => toggleDay(day)}
                    className={
                      'rounded-lg border px-1 py-2 text-xs ' +
                      (usage.occupiedWeekdays[day]
                        ? 'border-brand-500 bg-brand-50 text-brand-700'
                        : 'border-border text-ink-soft')
                    }
                  >
                    {WEEKDAY_LABELS[day]}
                  </button>
                ))}
              </div>
              {noActiveDay && (
                <p className="mt-2 text-xs text-red-600" role="alert">
                  Au moins un jour doit être actif lorsque l'usage compte des occupants.
                </p>
              )}
            </fieldset>
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <Card title="Profil d'usage">
            <div className="grid grid-cols-3 gap-3">
              <StatTile icon="🏢" label="Type d'usage" value={USAGE_TYPES.find((u) => u.code === usage.usageType)?.label ?? '—'} />
              <StatTile icon="👥" label="Occupation maximale" value={`${usage.maximumOccupants} personnes`} />
              <StatTile icon="🕐" label="Plage horaire" value={`${usage.occupancyStartHour}h - ${usage.occupancyEndHour}h`} />
              <StatTile icon="📅" label="Jours actifs" value={`${activeDaysCount} / 7`} />
              <StatTile icon="⏱️" label="Heures occupées / jour" value={`${occupiedHours.toFixed(1)} h`} />
              <StatTile
                icon="📐"
                label="Densité (indicatif)"
                value={densityM2PerPerson != null ? `${densityM2PerPerson.toFixed(1)} m²/pers.` : '—'}
              />
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

      <WizardFooter
        nextSteps={defaultNextSteps}
        onBack={goToPrevious}
        onContinue={goToNext}
        continueDisabled={noActiveDay || usage.maximumOccupants < usage.usualOccupants}
      />
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
