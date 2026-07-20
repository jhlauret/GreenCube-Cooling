import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { Facade, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';
import { facadeGrossAreaM2 } from '../../sync/syncStudy';

const FACADE_LABELS: Record<Facade, string> = { north: 'Nord', south: 'Sud', east: 'Est', west: 'Ouest' };
/** Keys must match sync/syncStudy.ts's PROTECTION_TYPE_CONFIG exactly —
 * each has a distinct backend shading_type and efficiency, sorted here by
 * that efficiency so the "protection appliquée" hint below reads naturally. */
const PROTECTIONS: { label: string; efficiencyPercent: number }[] = [
  { label: 'Stores intérieurs', efficiencyPercent: 15 },
  { label: 'Ombrage naturel', efficiencyPercent: 25 },
  { label: 'Casquette solaire', efficiencyPercent: 35 },
  { label: 'Brise-soleil', efficiencyPercent: 40 },
  { label: 'Stores extérieurs', efficiencyPercent: 50 },
];

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
              {orientation.facades.map((f) => {
                const wallAreaM2 = facadeGrossAreaM2(f.facade, study);
                return (
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
                    Surface vitrée (m²) — mur : {wallAreaM2.toFixed(1)} m²
                    <input
                      type="number"
                      step="0.5"
                      min={0}
                      max={wallAreaM2}
                      value={f.glazedAreaM2}
                      disabled={!f.enabled}
                      onChange={(e) => {
                        const raw = Number(e.target.value);
                        if (Number.isFinite(raw)) setGlazedArea(f.facade, Math.min(wallAreaM2, Math.max(0, raw)));
                      }}
                      className="mt-1 w-full rounded-lg border border-border px-2 py-1.5 text-sm outline-none focus:border-brand-500 disabled:bg-surface-muted"
                    />
                  </label>
                </div>
                );
              })}
            </div>
          </Card>

          <Card title="Protections solaires prévues">
            <div className="flex flex-wrap gap-2">
              {PROTECTIONS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => toggleProtection(p.label)}
                  className={
                    'rounded-full border px-3 py-1.5 text-sm ' +
                    (orientation.solarProtections.includes(p.label)
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-border text-ink-soft hover:border-brand-300')
                  }
                >
                  {p.label} ({p.efficiencyPercent} %)
                  {orientation.solarProtections.includes(p.label) && ' ✓'}
                </button>
              ))}
            </div>
            {orientation.solarProtections.length > 1 && (
              <p className="mt-3 text-xs text-ink-faint">
                Plusieurs protections sélectionnées : seule la plus efficace (
                {[...orientation.solarProtections].sort(
                  (a, b) =>
                    (PROTECTIONS.find((p) => p.label === b)?.efficiencyPercent ?? 0) -
                    (PROTECTIONS.find((p) => p.label === a)?.efficiencyPercent ?? 0),
                )[0]}
                ) est appliquée au calcul — le cumul de plusieurs dispositifs n'est pas encore modélisé.
              </p>
            )}
          </Card>
        </div>

        <Card title="Impact solaire estimé">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatTile icon="🧭" label="Façade la plus exposée" value={mostExposed ? FACADE_LABELS[mostExposed.facade] : '—'} />
            <StatTile icon="🪟" label="Surface vitrée totale" value={`${totalGlazedArea.toFixed(1)} m²`} />
            <StatTile
              icon="🛡️"
              label="Protection appliquée"
              value={
                orientation.solarProtections.length === 0
                  ? 'Aucune'
                  : `${[...orientation.solarProtections].sort(
                      (a, b) =>
                        (PROTECTIONS.find((p) => p.label === b)?.efficiencyPercent ?? 0) -
                        (PROTECTIONS.find((p) => p.label === a)?.efficiencyPercent ?? 0),
                    )[0]} (${Math.max(
                      ...orientation.solarProtections.map(
                        (label) => PROTECTIONS.find((p) => p.label === label)?.efficiencyPercent ?? 0,
                      ),
                    )} %)`
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
