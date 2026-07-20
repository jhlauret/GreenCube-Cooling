import { useEffect, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useWizardNav } from '../useWizardNav';
import type { StudyDraft } from '../../types/study';
import { useStudyStore } from '../../store/studyStore';
import { syncStudyToBackend } from '../../sync/syncStudy';
import {
  calculate,
  confirmAssumptions,
  createRevision,
  getStudy,
  getValidation,
  validateStudy,
  type BackendStudySummary,
  type ValidationReport,
} from '../../api/study';
import { loadStudyFromBackend } from '../../sync/syncStudy';
import { ApiError } from '../../api/client';

const PROVENANCE_DISPLAY: Record<string, { label: string; tone: 'brand' | 'warn' | 'neutral' }> = {
  catalog: { label: 'Catalogue', tone: 'brand' },
  api: { label: 'Mesurée (API)', tone: 'brand' },
  user_confirmed: { label: 'Confirmée par vous', tone: 'brand' },
  estimated_reference: { label: 'Estimée (valeur de référence)', tone: 'warn' },
  estimated_manual: { label: 'Estimée (saisie manuelle)', tone: 'warn' },
  missing_fallback: { label: 'Manquante (repli)', tone: 'warn' },
};

export function ReviewStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const { goToPrevious } = useWizardNav('review');
  const patchSilently = useStudyStore((state) => state.patchSilently);
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const navigate = useNavigate();

  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [backendStudy, setBackendStudy] = useState<BackendStudySummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [lifecycleBusy, setLifecycleBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setSyncError(null);
      try {
        const backendId = await syncStudyToBackend(
          study,
          (id) => patchSilently(study.id, { backendId: id }),
          (equipment) => patchSilently(study.id, { equipment }),
        );
        const [report, summary] = await Promise.all([getValidation(backendId), getStudy(backendId)]);
        if (!cancelled) {
          setValidation(report);
          setBackendStudy(summary);
        }
      } catch (err) {
        if (!cancelled) {
          setSyncError(err instanceof ApiError ? err.message : "Impossible de contacter l'API GreenCube Cooling.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [study.id]);

  async function handleValidateStudy() {
    if (!study.backendId) return;
    setLifecycleBusy(true);
    setSyncError(null);
    try {
      const summary = await validateStudy(study.backendId);
      setBackendStudy(summary);
    } catch (err) {
      setSyncError(err instanceof ApiError ? err.message : "Impossible de valider l'étude.");
    } finally {
      setLifecycleBusy(false);
    }
  }

  /** A validated study is locked: further edits require a new revision.
   * The local draft switches to track the new revision's backend id — from
   * the user's point of view they keep editing "the same" study, which now
   * happens to be revision N+1 (audit P1-07: revision/history exposed in
   * the frontend, not only reachable via direct Odoo backend access). */
  async function handleCreateRevision() {
    if (!study.backendId) return;
    setLifecycleBusy(true);
    setSyncError(null);
    try {
      const summary = await createRevision(study.backendId);
      const patch = await loadStudyFromBackend(summary.id);
      updateStudy(study.id, { ...patch, backendId: summary.id });
      setBackendStudy(summary);
      const report = await getValidation(summary.id);
      setValidation(report);
    } catch (err) {
      setSyncError(err instanceof ApiError ? err.message : 'Impossible de créer une révision.');
    } finally {
      setLifecycleBusy(false);
    }
  }

  const glazedArea = study.orientation.facades.filter((f) => f.enabled).reduce((s, f) => s + f.glazedAreaM2, 0);

  async function handleConfirmAssumptions() {
    if (!study.backendId) return;
    setLoading(true);
    try {
      await confirmAssumptions(study.backendId);
      const report = await getValidation(study.backendId);
      setValidation(report);
    } finally {
      setLoading(false);
    }
  }

  async function handleCalculate() {
    setCalculating(true);
    setSyncError(null);
    try {
      const backendId = await syncStudyToBackend(
        study,
        (id) => patchSilently(study.id, { backendId: id }),
        (equipment) => patchSilently(study.id, { equipment }),
      );
      const idempotencyKey = crypto.randomUUID();
      const job = await calculate(backendId, idempotencyKey);
      navigate(`/cooling/studies/${study.id}/results`, { state: { resultId: job.result_id } });
    } catch (err) {
      setSyncError(err instanceof ApiError ? err.message : "Impossible de lancer le calcul.");
    } finally {
      setCalculating(false);
    }
  }

  const reliabilityPercent = validation ? Math.round(validation.completeness_score * 100) : null;
  const blockingIssues = validation?.issues.filter((i) => i.blocking) ?? [];
  const warningIssues = validation?.issues.filter((i) => !i.blocking && i.severity === 'warning') ?? [];
  const hasNonConfirmedAssumptions = Object.entries(validation?.provenance_summary ?? {}).some(
    ([key, count]) => key !== 'catalog' && key !== 'api' && key !== 'user_confirmed' && count > 0,
  );

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h1 className="text-xl font-semibold text-ink">Vérifiez les données avant le calcul BTU</h1>
            <p className="mt-1 text-sm text-ink-soft">
              Cette synthèse et le score de fiabilité proviennent de la validation structurée du backend
              (GET /studies/&lt;id&gt;/validation), pas d'une estimation locale.
            </p>
          </div>
          <div className="w-full sm:w-64">
            <div className="flex items-baseline justify-between text-sm">
              <span className="text-ink-faint">Complétude des données (avant calcul)</span>
              <span className="text-lg font-semibold text-brand-700">
                {reliabilityPercent === null ? (loading ? '…' : '—') : `${reliabilityPercent} %`}
              </span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-surface-muted">
              <div className="h-full bg-brand-600" style={{ width: `${reliabilityPercent ?? 0}%` }} />
            </div>
          </div>
        </div>
        {syncError && <p className="mt-3 text-sm text-red-600">{syncError}</p>}
      </Card>

      {backendStudy && (
        <Card className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3">
            <Badge tone={backendStudy.state === 'validated' ? 'brand' : 'neutral'}>
              {backendStudy.state === 'validated'
                ? 'Validée'
                : backendStudy.state === 'calculated'
                  ? 'Calculée'
                  : backendStudy.state === 'ready'
                    ? 'Prête'
                    : backendStudy.state === 'incomplete'
                      ? 'Incomplète'
                      : 'Brouillon'}
            </Badge>
            <span className="text-sm text-ink-soft">
              Révision {backendStudy.revision_number}
              {backendStudy.parent_study_id && ' (créée à partir d\'une étude verrouillée)'}
            </span>
          </div>
          {backendStudy.state === 'calculated' && (
            <Button variant="secondary" disabled={lifecycleBusy} onClick={() => void handleValidateStudy()}>
              {lifecycleBusy ? 'Validation…' : 'Valider cette étude (verrouille les données)'}
            </Button>
          )}
          {backendStudy.state === 'validated' && (
            <Button variant="secondary" disabled={lifecycleBusy} onClick={() => void handleCreateRevision()}>
              {lifecycleBusy ? 'Création…' : 'Créer une révision pour continuer à modifier'}
            </Button>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ReviewCard title="Site" confirmed={study.location.climateConfirmed}>
          <ReviewRow label="Adresse" value={study.location.address || '—'} />
          <ReviewRow
            label="Coordonnées"
            value={study.location.latitude != null ? `${study.location.latitude.toFixed(4)}, ${study.location.longitude?.toFixed(4)}` : '—'}
          />
          <ReviewRow label="Altitude" value={study.location.altitudeM != null ? `${study.location.altitudeM} m` : '—'} />
        </ReviewCard>

        <ReviewCard title="GreenCube" confirmed>
          <ReviewRow label="Modèle" value={study.model.modelCode} />
          <ReviewRow
            label="Dimensions"
            value={`${study.model.lengthM} x ${study.model.widthM} x ${study.model.heightM} m`}
          />
          <ReviewRow label="U moyen" value={`${study.model.uValueWm2k} W/m².K`} />
        </ReviewCard>

        <ReviewCard title="Orientation & vitrages" confirmed={glazedArea > 0}>
          <ReviewRow label="Orientation" value={study.orientation.mainOrientation} />
          <ReviewRow label="Surface vitrée" value={`${glazedArea.toFixed(1)} m²`} />
          <ReviewRow label="Protections" value={study.orientation.solarProtections.length ? study.orientation.solarProtections.join(', ') : 'Aucune'} />
        </ReviewCard>

        <ReviewCard title="Usage" confirmed>
          <ReviewRow label="Type" value={study.usage.usageType} />
          <ReviewRow label="Occupation" value={`${study.usage.usualOccupants} personnes`} />
          <ReviewRow label="Horaires" value={`${study.usage.occupancyStartHour}h - ${study.usage.occupancyEndHour}h`} />
        </ReviewCard>

        <ReviewCard title="Équipements" estimated>
          <ReviewRow label="Nombre" value={`${study.equipment.length} équipements`} />
          <ReviewRow
            label="Puissance simultanée"
            value={`${(study.equipment.reduce((s, e) => s + e.quantity * e.unitPowerW * (e.simultaneityPercent / 100), 0) / 1000).toFixed(2)} kW`}
          />
        </ReviewCard>

        <ReviewCard title="Ventilation" estimated>
          <ReviewRow label="Type" value={study.comfort.ventilationSystem} />
          <ReviewRow label="Débit" value={`${study.comfort.estimatedAirflowM3h} m³/h`} />
        </ReviewCard>

        <ReviewCard title="Confort" estimated>
          <ReviewRow
            label="Température"
            value={`${study.comfort.targetTemperatureMinC}–${study.comfort.targetTemperatureMaxC} °C`}
          />
          <ReviewRow label="Humidité" value={`${study.comfort.targetHumidityPercent} %`} />
          <ReviewRow label="Niveau de service" value={study.comfort.serviceLevel} />
        </ReviewCard>

        <Card title="Points d'attention" className="sm:col-span-2 lg:col-span-1">
          {blockingIssues.length === 0 && warningIssues.length === 0 ? (
            <p className="text-sm text-ink-soft">{loading ? 'Analyse en cours…' : 'Aucun point d\'attention détecté.'}</p>
          ) : (
            <div className="flex flex-col gap-2">
              {[...blockingIssues, ...warningIssues].map((issue) => (
                <div key={issue.code + (issue.field_path ?? '')} className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-ink-soft">⚠ {issue.message}</span>
                  <Badge tone={issue.blocking ? 'warn' : 'neutral'}>{issue.blocking ? 'Bloquant' : 'Info'}</Badge>
                </div>
              ))}
            </div>
          )}
          {hasNonConfirmedAssumptions && study.backendId && (
            <Button variant="secondary" className="mt-3 w-fit" onClick={handleConfirmAssumptions} disabled={loading}>
              Confirmer les hypothèses non mesurées
            </Button>
          )}
        </Card>

        {validation && Object.keys(validation.provenance_summary).length > 0 && (
          <Card title="Provenance des données utilisées" className="sm:col-span-2 lg:col-span-1">
            <p className="mb-2 text-xs text-ink-faint">
              Répartition des lignes d'occupation, équipements, ventilation et protections par origine —
              renvoyée par le backend, pas une estimation locale.
            </p>
            <div className="flex flex-col gap-1.5 text-sm">
              {Object.entries(validation.provenance_summary).map(([code, count]) => {
                const display = PROVENANCE_DISPLAY[code] ?? { label: code, tone: 'neutral' as const };
                return (
                  <div key={code} className="flex items-center justify-between gap-2">
                    <Badge tone={display.tone}>{display.label}</Badge>
                    <span className="text-ink-soft">{count}</span>
                  </div>
                );
              })}
            </div>
          </Card>
        )}
      </div>

      <Card>
        <p className="text-sm font-medium text-ink">Champs affichés mais non utilisés par le calcul</p>
        <p className="mt-1 text-sm text-ink-soft">
          Composition des murs, isolation (mm) et type de vitrage (étape Modèle) sont affichés à titre
          indicatif mais ne sont pas transmis au solver MERCURE aujourd'hui — seul le coefficient U moyen
          l'est. Ces champs portent la mention « ℹ️ non utilisé dans le calcul » dans leur étape.
        </p>
      </Card>

      <Card className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-medium text-ink">✅ Synthèse prête pour le solver</p>
          <p className="mt-1 text-sm text-ink-soft">
            Le solver MERCURE (backend Odoo) utilisera ces données pour estimer la puissance de refroidissement
            (BTU/h) et proposer le dimensionnement recommandé.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={goToPrevious}>
            ← Retour
          </Button>
          <Button onClick={handleCalculate} disabled={calculating || blockingIssues.length > 0}>
            {calculating ? 'Calcul en cours…' : 'Calculer la puissance de refroidissement →'}
          </Button>
        </div>
      </Card>
    </div>
  );
}

function ReviewCard({
  title,
  confirmed,
  estimated,
  children,
}: {
  title: string;
  confirmed?: boolean;
  estimated?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card
      title={title}
      action={
        confirmed ? <Badge tone="brand">Confirmé</Badge> : estimated ? <Badge tone="warn">Estimé</Badge> : undefined
      }
    >
      <div className="flex flex-col gap-1.5 text-sm">{children}</div>
    </Card>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-ink-faint">{label}</span>
      <span className="text-right font-medium text-ink">{value}</span>
    </div>
  );
}
