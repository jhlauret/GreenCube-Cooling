import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { Facade, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';

const FACADE_LABELS: Record<Facade, string> = { north: 'Nord', south: 'Sud', east: 'Est', west: 'Ouest' };
const PROTECTIONS = ['Stores intérieurs', 'Stores extérieurs', 'Brise-soleil', 'Casquette solaire', 'Ombrage naturel'];

export function OrientationStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('orientation');
  const { orientation } = study;

  function toggleFacade(facade: Facade) {
    updateStudy(studyId, {
      orientation: {
        ...orientation,
        facades: orientation.facades.map((f) => (f.facade === facade ? { ...f, enabled: !f.enabled } : f)),
      },
    });
  }

  function setGlazedArea(facade: Facade, areaM2: number) {
    updateStudy(studyId, {
      orientation: {
        ...orientation,
        facades: orientation.facades.map((f) => (f.facade === facade ? { ...f, glazedAreaM2: areaM2 } : f)),
      },
    });
  }

  function toggleProtection(protection: string) {
    const has = orientation.solarProtections.includes(protection);
    updateStudy(studyId, {
      orientation: {
        ...orientation,
        solarProtections: has
          ? orientation.solarProtections.filter((p) => p !== protection)
          : [...orientation.solarProtections, protection],
      },
    });
  }

  const totalGlazedArea = orientation.facades.filter((f) => f.enabled).reduce((sum, f) => sum + f.glazedAreaM2, 0);
  const mostExposed = orientation.facades.filter((f) => f.enabled).sort((a, b) => b.glazedAreaM2 - a.glazedAreaM2)[0];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <Card title="Comment votre GreenCube est-il orienté ?">
            <div className="grid grid-cols-4 gap-2">
              {(['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'] as const).map((dir) => (
                <button
                  key={dir}
                  onClick={() => updateStudy(studyId, { orientation: { ...orientation, mainOrientation: dir } })}
                  className={
                    'rounded-lg border px-2 py-2 text-sm ' +
                    (orientation.mainOrientation === dir
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-border text-ink-soft hover:border-brand-300')
                  }
                >
                  {dir}
                </button>
              ))}
            </div>
          </Card>

          <Card title="Façades et surfaces vitrées">
            <div className="grid grid-cols-2 gap-3">
              {orientation.facades.map((f) => (
                <div
                  key={f.facade}
                  className={
                    'rounded-xl border p-4 ' + (f.enabled ? 'border-brand-500' : 'border-border')
                  }
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-ink">{FACADE_LABELS[f.facade]}</span>
                    <button
                      role="switch"
                      aria-checked={f.enabled}
                      onClick={() => toggleFacade(f.facade)}
                      className={
                        'h-5 w-9 rounded-full transition-colors ' + (f.enabled ? 'bg-brand-600' : 'bg-border')
                      }
                    >
                      <span
                        className={
                          'block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform ' +
                          (f.enabled ? 'translate-x-4' : '')
                        }
                      />
                    </button>
                  </div>
                  <label className="text-xs text-ink-faint">
                    Surface vitrée (m²)
                    <input
                      type="number"
                      step="0.5"
                      value={f.glazedAreaM2}
                      disabled={!f.enabled}
                      onChange={(e) => setGlazedArea(f.facade, Number(e.target.value))}
                      className="mt-1 w-full rounded-lg border border-border px-2 py-1.5 text-sm outline-none focus:border-brand-500 disabled:bg-surface-muted"
                    />
                  </label>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Protections solaires prévues">
            <div className="flex flex-wrap gap-2">
              {PROTECTIONS.map((p) => (
                <button
                  key={p}
                  onClick={() => toggleProtection(p)}
                  className={
                    'rounded-full border px-3 py-1.5 text-sm ' +
                    (orientation.solarProtections.includes(p)
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-border text-ink-soft hover:border-brand-300')
                  }
                >
                  {p}
                  {orientation.solarProtections.includes(p) && ' ✓'}
                </button>
              ))}
            </div>
          </Card>
        </div>

        <Card title="Impact solaire estimé">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatTile icon="🧭" label="Façade la plus exposée" value={mostExposed ? FACADE_LABELS[mostExposed.facade] : '—'} />
            <StatTile icon="🪟" label="Surface vitrée totale" value={`${totalGlazedArea.toFixed(1)} m²`} />
            <StatTile
              icon="🛡️"
              label="Niveau de protection"
              value={
                orientation.protectionEfficiency === 'high'
                  ? 'Élevée'
                  : orientation.protectionEfficiency === 'medium'
                    ? 'Moyenne'
                    : 'Faible'
              }
            />
          </div>
          <p className="mt-4 text-sm text-ink-soft">
            La visualisation 3D et la trajectoire solaire détaillée seront disponibles une fois le module de rendu connecté au backend.
          </p>
        </Card>
      </div>

      <WizardFooter nextSteps={defaultNextSteps} onBack={goToPrevious} onContinue={goToNext} />
    </div>
  );
}
