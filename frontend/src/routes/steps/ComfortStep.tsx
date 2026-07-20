import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { ComfortData, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';

const VENTILATION_SYSTEMS: { code: ComfortData['ventilationSystem']; label: string; icon: string }[] = [
  { code: 'natural', label: 'Ventilation naturelle', icon: '🍃' },
  { code: 'simple_flow', label: 'VMC simple flux', icon: '🔄' },
  { code: 'double_flow', label: 'VMC double flux', icon: '⇄' },
  { code: 'dedicated_mechanical', label: 'Ventilation mécanique dédiée', icon: '💨' },
];

const SERVICE_LEVELS: { code: ComfortData['serviceLevel']; label: string; description: string }[] = [
  { code: 'standard', label: 'Confort standard', description: 'Conditions de confort usuelles pour la majorité des situations climatiques.' },
  { code: 'enhanced', label: 'Confort renforcé', description: 'Meilleur confort thermique et qualité d\'air améliorée. Recommandé pour les usages exigeants.' },
  { code: 'heatwave_resilience', label: 'Résilience canicule', description: 'Conçu pour maintenir le confort lors d\'épisodes de chaleur intense.' },
];

export function ComfortStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('comfort');
  const { comfort } = study;

  function patch(fields: Partial<ComfortData>) {
    updateStudy(studyId, { comfort: { ...comfort, ...fields } });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <Card title="Ventilation">
            <p className="mb-3 text-sm text-ink-soft">Système de ventilation</p>
            <div className="grid grid-cols-4 gap-2">
              {VENTILATION_SYSTEMS.map((v) => (
                <button
                  key={v.code}
                  onClick={() => patch({ ventilationSystem: v.code })}
                  className={
                    'flex flex-col items-center gap-1 rounded-xl border px-2 py-3 text-center text-xs ' +
                    (comfort.ventilationSystem === v.code
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-border text-ink-soft hover:border-brand-300')
                  }
                >
                  <span className="text-xl">{v.icon}</span>
                  {v.label}
                </button>
              ))}
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3">
              <LabeledNumber
                label="Débit d'air estimé (m³/h)"
                value={comfort.estimatedAirflowM3h}
                min={0}
                max={5000}
                onChange={(v) => patch({ estimatedAirflowM3h: v })}
              />
            </div>
          </Card>

          <Card title="Confort cible">
            <div className="grid grid-cols-3 gap-4">
              <LabeledNumber
                label="Température cible (°C)"
                value={comfort.targetTemperatureMinC}
                min={10}
                max={comfort.targetTemperatureMaxC}
                onChange={(v) => patch({ targetTemperatureMinC: v })}
              />
              <LabeledNumber
                label="Température maximale acceptable (°C)"
                value={comfort.targetTemperatureMaxC}
                min={comfort.targetTemperatureMinC}
                max={40}
                onChange={(v) => patch({ targetTemperatureMaxC: v })}
              />
              <LabeledNumber
                label="Humidité relative cible (%)"
                value={comfort.targetHumidityPercent}
                min={0}
                max={100}
                onChange={(v) => patch({ targetHumidityPercent: v })}
              />
            </div>
            <div className="mt-4 flex items-center justify-between">
              <span className="text-sm text-ink-soft">Utilisation la nuit</span>
              <div className="flex gap-2">
                <button
                  onClick={() => patch({ usedAtNight: true })}
                  className={
                    'rounded-lg border px-3 py-1.5 text-sm ' +
                    (comfort.usedAtNight ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-border text-ink-soft')
                  }
                >
                  Oui
                </button>
                <button
                  onClick={() => patch({ usedAtNight: false })}
                  className={
                    'rounded-lg border px-3 py-1.5 text-sm ' +
                    (!comfort.usedAtNight ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-border text-ink-soft')
                  }
                >
                  Non
                </button>
              </div>
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <Card title="Niveau de service">
            <div className="flex flex-col gap-3">
              {SERVICE_LEVELS.map((s) => (
                <button
                  key={s.code}
                  onClick={() => patch({ serviceLevel: s.code })}
                  className={
                    'rounded-xl border p-4 text-left ' +
                    (comfort.serviceLevel === s.code ? 'border-brand-500 bg-brand-50' : 'border-border hover:border-brand-300')
                  }
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-ink">{s.label}</span>
                    {comfort.serviceLevel === s.code && <span className="text-brand-600">✓</span>}
                  </div>
                  <p className="mt-1 text-xs text-ink-soft">{s.description}</p>
                </button>
              ))}
            </div>
          </Card>

          <Card title="Synthèse des choix">
            <div className="grid grid-cols-3 gap-3">
              <StatTile
                icon="🌡️"
                label="Température cible"
                value={`${comfort.targetTemperatureMinC}–${comfort.targetTemperatureMaxC} °C`}
              />
              <StatTile icon="💨" label="Débit d'air retenu" value={`${comfort.estimatedAirflowM3h} m³/h`} />
              <StatTile
                icon="🛡️"
                label="Niveau de service"
                value={SERVICE_LEVELS.find((s) => s.code === comfort.serviceLevel)?.label ?? '—'}
              />
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
