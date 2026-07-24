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
        roofUValueWm2k: template.roof_u_value,
        floorUValueWm2k: template.floor_u_value,
        airtightnessN50: template.airtightness_n50,
      },
    });
  }

  /**
   * Whether the study's current values still match the catalog template it
   * was applied from. Compares only the fields the template actually
   * governs (GC-COOLING-08 pt.6: distinguish "inherited" from
   * "customized" so a modification is never silently lost or hidden).
   */
  function isCustomizedFromTemplate(template: BackendThermalSpecification): boolean {
    return (
      model.lengthM !== template.length_m ||
      model.widthM !== template.width_m ||
      model.heightM !== template.height_m ||
      model.uValueWm2k !== template.wall_u_value ||
      model.roofUValueWm2k !== template.roof_u_value ||
      model.floorUValueWm2k !== template.floor_u_value ||
      model.airtightnessN50 !== template.airtightness_n50
    );
  }

  const appliedTemplate = model.templateId ? templates.find((t) => t.id === model.templateId) : undefined;
  const customized = appliedTemplate ? isCustomizedFromTemplate(appliedTemplate) : false;
  const templateHasNewerVersion =
    appliedTemplate != null && model.templateVersion != null && appliedTemplate.version !== model.templateVersion;

  /**
   * Building the diff up front, and requiring an explicit confirmation
   * before applying it, is what GC-COOLING-08 pt.7/8 asks for: a template
   * reload/version bump must never silently overwrite a customization —
   * the user sees exactly which fields would change and confirms before
   * anything is touched.
   */
  function templateReapplyDiff(template: BackendThermalSpecification): string[] {
    const rows: [string, number, number, string][] = [
      ['Longueur', model.lengthM, template.length_m, 'm'],
      ['Largeur', model.widthM, template.width_m, 'm'],
      ['Hauteur', model.heightM, template.height_m, 'm'],
      ['U murs', model.uValueWm2k, template.wall_u_value, 'W/m².K'],
      ['U toiture', model.roofUValueWm2k, template.roof_u_value, 'W/m².K'],
      ['U plancher', model.floorUValueWm2k, template.floor_u_value, 'W/m².K'],
      ['Étanchéité n50', model.airtightnessN50, template.airtightness_n50, 'vol/h'],
    ];
    return rows
      .filter(([, current, next]) => current !== next)
      .map(([label, current, next, unit]) => `${label} : ${current} -> ${next} ${unit}`);
  }

  function reapplyTemplate() {
    if (!appliedTemplate) return;
    const diff = templateReapplyDiff(appliedTemplate);
    if (diff.length > 0) {
      const confirmed = window.confirm(
        `Réappliquer le modèle catalogue « ${appliedTemplate.code} » (v${appliedTemplate.version}) va remplacer les valeurs suivantes :\n\n` +
          diff.join('\n') +
          '\n\nContinuer ?',
      );
      if (!confirmed) return;
    }
    const presentation = MODEL_PRESENTATION.find((m) => m.catalogCode === appliedTemplate.code);
    applyTemplate(appliedTemplate, presentation?.code ?? model.modelCode);
  }

  function selectCustom() {
    // Deliberately keeps templateId/templateVersion untouched: if a catalog
    // model was already applied, switching to "Personnalisé" here means
    // "customize this GreenCube for this study" (GC-COOLING-08
    // "Personnalisation d'un modèle catalogue" — the study keeps a fork of
    // the template, source_template_id stays set on the backend, and the
    // UI must keep showing which template it diverged from). Only a study
    // that never had a template applied ends up with a plain, unattributed
    // custom configuration.
    updateStudy(studyId, { model: { ...model, modelCode: 'custom' } });
  }

  function setDimension(field: 'lengthM' | 'widthM' | 'heightM', value: number) {
    updateStudy(studyId, { model: { ...model, [field]: value } });
  }

  function setEnvelope(field: 'uValueWm2k' | 'roofUValueWm2k' | 'floorUValueWm2k', value: number) {
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
                <p className="mb-2 mt-4 text-sm font-medium text-ink">Valeurs U (W/m².K)</p>
                <div className="grid grid-cols-3 gap-3">
                  <LabeledNumber
                    label="Murs"
                    value={model.uValueWm2k}
                    min={0.05}
                    max={6}
                    step={0.01}
                    onChange={(v) => setEnvelope('uValueWm2k', v)}
                  />
                  <LabeledNumber
                    label="Toiture"
                    value={model.roofUValueWm2k}
                    min={0.05}
                    max={6}
                    step={0.01}
                    onChange={(v) => setEnvelope('roofUValueWm2k', v)}
                  />
                  <LabeledNumber
                    label="Plancher"
                    value={model.floorUValueWm2k}
                    min={0.05}
                    max={6}
                    step={0.01}
                    onChange={(v) => setEnvelope('floorUValueWm2k', v)}
                  />
                </div>
              </div>
            )}

            {appliedTemplate && (
              <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-surface-muted p-3 text-xs">
                {customized ? (
                  <span className="rounded-full bg-amber-100 px-2 py-1 font-medium text-amber-800">
                    Modifié pour cette étude
                  </span>
                ) : (
                  <span className="rounded-full bg-brand-50 px-2 py-1 font-medium text-brand-700">
                    Valeurs héritées du catalogue Odoo (v{appliedTemplate.version})
                  </span>
                )}
                {templateHasNewerVersion && (
                  <span className="text-ink-soft">
                    Une version plus récente du modèle catalogue existe (v{appliedTemplate.version}).
                  </span>
                )}
                {(customized || templateHasNewerVersion) && (
                  <button
                    type="button"
                    onClick={reapplyTemplate}
                    className="ml-auto rounded-lg border border-brand-300 px-3 py-1 font-medium text-brand-700 hover:bg-brand-50"
                  >
                    Réappliquer le modèle catalogue
                  </button>
                )}
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
              <dt className="text-ink-faint">Coefficient U murs</dt>
              <dd className="text-right font-medium text-ink">{model.uValueWm2k.toFixed(2)} W/m².K</dd>
              <dt className="text-ink-faint">Coefficient U toiture</dt>
              <dd className="text-right font-medium text-ink">{model.roofUValueWm2k.toFixed(2)} W/m².K</dd>
              <dt className="text-ink-faint">Coefficient U plancher</dt>
              <dd className="text-right font-medium text-ink">{model.floorUValueWm2k.toFixed(2)} W/m².K</dd>
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
  step = 0.1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-soft">
      {label}
      <input
        type="number"
        step={step}
        min={min}
        max={max}
        value={value}
        onChange={(e) => {
          // Deliberately does NOT clamp on every keystroke: this is a
          // controlled input, so re-rendering it with a clamped value
          // mid-typing (e.g. typing "0.33" one character at a time, where
          // "0" alone would clamp to `min`) rewrites the field's text out
          // from under the user's cursor and corrupts what they're typing.
          // Bounds are enforced on blur instead, and always server-side
          // (api_validation.FIELD_LIMITS) regardless of what the UI does.
          const raw = Number(e.target.value);
          if (Number.isFinite(raw)) onChange(raw);
        }}
        onBlur={(e) => {
          const raw = Number(e.target.value);
          if (Number.isFinite(raw)) onChange(Math.min(max, Math.max(min, raw)));
        }}
        className="rounded-lg border border-border px-3 py-2 text-sm text-ink outline-none focus:border-brand-500"
      />
    </label>
  );
}
