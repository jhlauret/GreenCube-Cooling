import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { GreenCubeModelCode, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';

const MODELS: { code: GreenCubeModelCode; label: string; description: string; icon: string }[] = [
  { code: 'studio', label: 'GreenCube Studio', description: "Module compact idéal pour un espace de travail ou de vie individuel.", icon: '🏠' },
  { code: 'office', label: 'GreenCube Bureau', description: 'Espace professionnel optimisé pour le confort et la productivité.', icon: '🏢' },
  { code: 'living', label: 'GreenCube Habitat', description: 'Habitat modulaire confortable, performant et durable.', icon: '🏡' },
  { code: 'commerce', label: 'GreenCube Commerce', description: 'Espace commercial modulable pour accueillir vos activités.', icon: '🏬' },
  { code: 'custom', label: 'GreenCube Personnalisé', description: 'Définissez vos propres dimensions et caractéristiques.', icon: '📐' },
];

export function ModelStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('model');

  const { model } = study;
  const floorAreaM2 = model.lengthM * model.widthM;
  const volumeM3 = floorAreaM2 * model.heightM;

  function selectModel(code: GreenCubeModelCode) {
    updateStudy(studyId, { model: { ...model, modelCode: code } });
  }

  function setDimension(field: 'lengthM' | 'widthM' | 'heightM', value: number) {
    updateStudy(studyId, { model: { ...model, [field]: value } });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Card title="Quel GreenCube souhaitez-vous climatiser ?">
          <div className="flex flex-col gap-3">
            {MODELS.map((m) => {
              const selected = model.modelCode === m.code;
              return (
                <button
                  key={m.code}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => selectModel(m.code)}
                  className={
                    'flex items-center gap-3 rounded-xl border p-4 text-left transition-colors ' +
                    (selected ? 'border-brand-500 bg-brand-50' : 'border-border hover:border-brand-300')
                  }
                >
                  <span className="text-2xl">{m.icon}</span>
                  <span>
                    <span className="block text-sm font-medium text-ink">{m.label}</span>
                    <span className="block text-xs text-ink-soft">{m.description}</span>
                  </span>
                  {selected && <span className="ml-auto text-brand-600">✓</span>}
                </button>
              );
            })}

            {model.modelCode === 'custom' && (
              <div className="mt-2 rounded-xl border border-border p-4">
                <p className="mb-3 text-sm font-medium text-ink">Mode personnalisé</p>
                <div className="grid grid-cols-3 gap-3">
                  <LabeledNumber label="Longueur (m)" value={model.lengthM} onChange={(v) => setDimension('lengthM', v)} />
                  <LabeledNumber label="Largeur (m)" value={model.widthM} onChange={(v) => setDimension('widthM', v)} />
                  <LabeledNumber label="Hauteur (m)" value={model.heightM} onChange={(v) => setDimension('heightM', v)} />
                </div>
              </div>
            )}
          </div>
        </Card>

        <div className="flex flex-col gap-4">
          <Card title="Spécifications du modèle">
            <dl className="grid grid-cols-2 gap-y-3 text-sm">
              <dt className="text-ink-faint">Dimensions (L x l x h)</dt>
              <dd className="text-right font-medium text-ink">
                {model.lengthM.toFixed(2)} x {model.widthM.toFixed(2)} x {model.heightM.toFixed(2)} m
              </dd>
              <dt className="text-ink-faint">Surface intérieure</dt>
              <dd className="text-right font-medium text-ink">{floorAreaM2.toFixed(2)} m²</dd>
              <dt className="text-ink-faint">Volume intérieur</dt>
              <dd className="text-right font-medium text-ink">{volumeM3.toFixed(2)} m³</dd>
              <dt className="text-ink-faint">Composition des murs</dt>
              <dd className="text-right font-medium text-ink">{model.wallComposition}</dd>
              <dt className="text-ink-faint">Isolation</dt>
              <dd className="text-right font-medium text-ink">{model.insulationMm} mm</dd>
              <dt className="text-ink-faint">Vitrage</dt>
              <dd className="text-right font-medium text-ink">{model.glazingType}</dd>
              <dt className="text-ink-faint">Coefficient U (moyen)</dt>
              <dd className="text-right font-medium text-ink">{model.uValueWm2k.toFixed(2)} W/m².K</dd>
              <dt className="text-ink-faint">Étanchéité à l'air</dt>
              <dd className="text-right font-medium text-ink">{model.airtightnessN50} vol/h</dd>
            </dl>
          </Card>

          <Card title="Résumé du modèle">
            <div className="grid grid-cols-3 gap-3">
              <StatTile icon="📏" label="Surface intérieure" value={`${floorAreaM2.toFixed(2)} m²`} valueClassName="text-brand-700" />
              <StatTile icon="📦" label="Volume intérieur" value={`${volumeM3.toFixed(2)} m³`} valueClassName="text-brand-700" />
              <StatTile icon="🌡️" label="U moyen" value={`${model.uValueWm2k.toFixed(2)} W/m².K`} valueClassName="text-brand-700" />
            </div>
          </Card>
        </div>
      </div>

      <WizardFooter nextSteps={defaultNextSteps} onBack={goToPrevious} onContinue={goToNext} />
    </div>
  );
}

function LabeledNumber({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-soft">
      {label}
      <input
        type="number"
        step="0.1"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="rounded-lg border border-border px-3 py-2 text-sm text-ink outline-none focus:border-brand-500"
      />
    </label>
  );
}
