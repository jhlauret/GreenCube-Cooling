import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatTile } from '../../components/ui/StatTile';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { GreenCubeModelCode, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';
import { getThermalSpecificationTemplates, type BackendThermalSpecification } from '../../api/study';

/** Presentation only (icon/label) — the code->catalog-code mapping ties a
 * card to its real Odoo template; every value used for calculation comes
 * from the fetched template, never from this array (GC-COOLING-08). */
const MODEL_PRESENTATION: { code: GreenCubeModelCode; catalogCode: string; label: string; icon: string }[] = [
  { code: 'studio', catalogCode: 'gc-studio', label: 'GreenCube Studio', icon: '🏠' },
  { code: 'office', catalogCode: 'gc-office', label: 'GreenCube Bureau', icon: '🏢' },
  { code: 'living', catalogCode: 'gc-living', label: 'GreenCube Habitat', icon: '🏡' },
  { code: 'commerce', catalogCode: 'gc-commerce', label: 'GreenCube Commerce', icon: '🏬' },
];

export function ModelStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('model');

  const { model } = study;
  const floorAreaM2 = model.lengthM * model.widthM;
  const volumeM3 = floorAreaM2 * model.heightM;

  const [templates, setTemplates] = useState<BackendThermalSpecification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getThermalSpecificationTemplates()
      .then((data) => {
        if (cancelled) return;
        setTemplates(data);
        // First time this draft ever sees the catalog and no template has
        // been applied yet: apply the default "studio" card so the
        // displayed dimensions actually match the pre-selected label
        // instead of local hardcoded defaults (audit P1-01).
        if (!model.templateId && model.modelCode !== 'custom') {
          const match = data.find((t) => t.code === `gc-${model.modelCode}`);
          if (match) applyTemplate(match, model.modelCode);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Impossible de charger le catalogue GreenCube.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function applyTemplate(template: BackendThermalSpecification, code: GreenCubeModelCode) {
    updateStudy(studyId, {
      model: {
        ...model,
        modelCode: code,
        templateId: template.id,
        templateVersion: template.version,
        lengthM: template.length_m,
        widthM: template.width_m,
        heightM: template.height_m,
        uValueWm2k: template.wall_u_value,
        airtightnessN50: template.airtightness_n50,
      },
    });
  }

  function selectCustom() {
    updateStudy(studyId, { model: { ...model, modelCode: 'custom', templateId: null, templateVersion: null } });
  }

  function setDimension(field: 'lengthM' | 'widthM' | 'heightM', value: number) {
    updateStudy(studyId, { model: { ...model, [field]: value } });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Card title="Quel GreenCube souhaitez-vous climatiser ?">
          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
          <div className="flex flex-col gap-3">
            {loading && templates.length === 0 && (
              <p className="text-sm text-ink-soft">Chargement du catalogue GreenCube (Odoo)…</p>
            )}
            {MODEL_PRESENTATION.map((m) => {
              const template = templates.find((t) => t.code === m.catalogCode);
              const selected = model.modelCode === m.code && model.templateId === (template?.id ?? null);
              return (
                <button
                  key={m.code}
                  type="button"
                  aria-pressed={selected}
                  disabled={!template}
                  onClick={() => template && applyTemplate(template, m.code)}
                  className={
                    'flex items-center gap-3 rounded-xl border p-4 text-left transition-colors disabled:opacity-40 ' +
                    (selected ? 'border-brand-500 bg-brand-50' : 'border-border hover:border-brand-300')
                  }
                >
                  <span className="text-2xl">{m.icon}</span>
                  <span>
                    <span className="block text-sm font-medium text-ink">{m.label}</span>
                    <span className="block text-xs text-ink-soft">
                      {template
                        ? `${template.length_m} x ${template.width_m} x ${template.height_m} m · U=${template.wall_u_value.toFixed(2)} W/m².K · v${template.version}`
                        : 'Modèle indisponible'}
                    </span>
                  </span>
                  {selected && <span className="ml-auto text-brand-600">✓</span>}
                </button>
              );
            })}
            <button
              type="button"
              aria-pressed={model.modelCode === 'custom'}
              onClick={selectCustom}
              className={
                'flex items-center gap-3 rounded-xl border p-4 text-left transition-colors ' +
                (model.modelCode === 'custom' ? 'border-brand-500 bg-brand-50' : 'border-border hover:border-brand-300')
              }
            >
              <span className="text-2xl">📐</span>
              <span>
                <span className="block text-sm font-medium text-ink">GreenCube Personnalisé</span>
                <span className="block text-xs text-ink-soft">Définissez vos propres dimensions et caractéristiques.</span>
              </span>
              {model.modelCode === 'custom' && <span className="ml-auto text-brand-600">✓</span>}
            </button>

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
              <dt className="text-ink-faint" title="Non utilisé dans le calcul MERCURE (indicatif uniquement)">
                Composition des murs ℹ️
              </dt>
              <dd className="text-right font-medium text-ink">{model.wallComposition}</dd>
              <dt className="text-ink-faint" title="Non utilisé dans le calcul MERCURE (indicatif uniquement)">
                Isolation ℹ️
              </dt>
              <dd className="text-right font-medium text-ink">{model.insulationMm} mm</dd>
              <dt className="text-ink-faint" title="Non utilisé dans le calcul MERCURE (indicatif uniquement)">
                Vitrage ℹ️
              </dt>
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

/**
 * min/max mirror the backend SQL CHECK constraints on
 * greencube.thermal.specification (length/width/height_m > 0) plus a
 * sane upper bound for a modular building dimension, so an obviously
 * invalid value is caught here instead of only surfacing as a generic
 * sync error after PUT /thermal-specification (audit GC-COOLING-06 pt.9).
 */
function LabeledNumber({
  label,
  value,
  onChange,
  min = 0.5,
  max = 20,
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
        step="0.1"
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
