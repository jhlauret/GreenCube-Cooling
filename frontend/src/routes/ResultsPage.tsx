import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useLocation, useParams } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { StatTile } from '../components/ui/StatTile';
import { useStudyStore } from '../store/studyStore';
import {
  calculate,
  getCalculationJob,
  getResult,
  getStudyResults,
  ENERGYPLUS_TERMINAL_STATUSES,
  type BackendResult,
  type CalculationJob,
} from '../api/study';
import { ApiError } from '../api/client';

const FACADE_LABELS_FR: Record<string, string> = { north: 'Nord', south: 'Sud', east: 'Est', west: 'Ouest' };

const ENERGYPLUS_STATUS_LABEL: Record<string, string> = {
  not_requested: 'EnergyPlus non demandé pour ce calcul.',
  disabled: 'EnergyPlus est désactivé sur ce serveur.',
  translation_failed: "La traduction du modèle pour EnergyPlus a échoué.",
  queued_for_worker: 'Simulation EnergyPlus en attente de traitement par le worker…',
  simulation_running: 'Simulation EnergyPlus en cours…',
  simulation_unavailable: "Le worker EnergyPlus n'était pas disponible pour ce calcul.",
  simulation_failed: 'La simulation EnergyPlus a échoué.',
  simulation_completed: 'Simulation EnergyPlus terminée.',
};

// Capped exponential backoff: real polling (per GC-COOLING-16), never a
// fixed tight interval — and it always stops once the EnergyPlus tail
// reaches a terminal status (ENERGYPLUS_TERMINAL_STATUSES), it never runs
// forever. MERCURE itself is synchronous by the time the page mounts, so
// there is nothing to poll for its own status — only the EnergyPlus
// hand-off (job.energyplus_processing_status) can still be pending.
const POLL_BACKOFF_MS = [3000, 5000, 8000, 15000, 30000];

/**
 * Never triggers a calculation itself on mount — POST /calculations only
 * ever runs from an explicit user action (ReviewStep's button, or this
 * page's own "Relancer le calcul" button below). This page just fetches
 * and displays the result it was navigated to (or the study's latest
 * result on a direct visit/refresh), so remounting or revisiting this
 * route can't spawn duplicate solver runs or history pollution
 * (audit P1-06).
 */
export function ResultsPage() {
  const { studyId } = useParams<{ studyId: string }>();
  const location = useLocation();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));

  const navState = location.state as { resultId?: number; jobId?: number } | null;
  const navigationResultId = navState?.resultId ?? null;
  const navigationJobId = navState?.jobId ?? null;

  const [result, setResult] = useState<BackendResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<CalculationJob | null>(null);
  const [activeJobId, setActiveJobId] = useState<number | null>(navigationJobId);
  const [rerunning, setRerunning] = useState(false);
  const [rerunError, setRerunError] = useState<string | null>(null);
  const pollAttempt = useRef(0);

  useEffect(() => {
    if (!study) return;
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        if (navigationResultId) {
          const computed = await getResult(navigationResultId);
          if (!cancelled) setResult(computed);
          return;
        }
        if (study!.backendId) {
          const results = await getStudyResults(study!.backendId);
          if (!cancelled) setResult(results[0] ?? null);
          if (!cancelled && results.length === 0) {
            setError("Aucun résultat pour cette étude. Lancez un calcul depuis l'étape de vérification.");
          }
          return;
        }
        if (!cancelled) {
          setError("Aucun résultat pour cette étude. Lancez un calcul depuis l'étape de vérification.");
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Impossible de récupérer le résultat du calcul.",
          );
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
  }, [study?.id, navigationResultId]);

  // Poll the calculation job only for the EnergyPlus hand-off tail, and
  // only when we actually arrived here from a fresh POST /calculations
  // (navigationJobId set). Visiting/refreshing this route later — e.g. to
  // consult a past result — never starts polling, since there is no job
  // reference to poll and no new calculation is ever implied by a GET.
  useEffect(() => {
    if (!activeJobId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    pollAttempt.current = 0;

    async function poll() {
      try {
        const current = await getCalculationJob(activeJobId!);
        if (cancelled) return;
        setJob(current);
        if (ENERGYPLUS_TERMINAL_STATUSES.includes(current.energyplus_processing_status)) {
          return; // Terminal: stop polling for good.
        }
        const delay = POLL_BACKOFF_MS[Math.min(pollAttempt.current, POLL_BACKOFF_MS.length - 1)];
        pollAttempt.current += 1;
        timer = setTimeout(() => void poll(), delay);
      } catch {
        // A transient polling failure must not crash the results screen —
        // the numeric result already loaded is still valid and displayed;
        // we simply stop trying to refresh the EnergyPlus tail status.
      }
    }
    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [activeJobId]);

  async function refreshFromLatest() {
    if (!study?.backendId) return;
    const results = await getStudyResults(study.backendId);
    if (results.length > 0) {
      setResult(results[0]);
      setError(null);
    }
  }

  /** Creates a brand-new job/result via a fresh Idempotency-Key — never
   * mutates the currently displayed (immutable) result. `rerunning` guards
   * against double-clicks firing two POSTs for the same intent. */
  async function handleRerun() {
    if (!study?.backendId || rerunning) return;
    setRerunning(true);
    setRerunError(null);
    try {
      const idempotencyKey = crypto.randomUUID();
      const newJob = await calculate(study.backendId, idempotencyKey);
      if (newJob.result_id == null) {
        throw new Error('Le backend a renvoyé un job sans résultat associé.');
      }
      const refreshed = await getResult(newJob.result_id);
      setResult(refreshed);
      setJob(null);
      setActiveJobId(newJob.job_id);
    } catch (err) {
      setRerunError(err instanceof ApiError ? err.message : 'Impossible de relancer le calcul.');
    } finally {
      setRerunning(false);
    }
  }

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader syncState={study.backendId ? 'synced' : 'local'} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-ink">Résultats — {study.name}</h1>
          <Link to={`/cooling/studies/${studyId}/review`} className="text-sm text-brand-700 hover:underline">
            ← Revenir à la vérification
          </Link>
        </div>

        {loading ? (
          <Card>
            <p className="text-sm text-ink-soft">Calcul en cours (moteur MERCURE, backend Odoo)…</p>
          </Card>
        ) : error || !result ? (
          <Card>
            <p className="text-sm text-red-600">{error ?? "Le calcul n'a pas pu être exécuté."}</p>
            <Button variant="secondary" className="mt-3" onClick={() => void refreshFromLatest()}>
              Réessayer
            </Button>
          </Card>
        ) : (
          <div className="flex flex-col gap-4">
            {!result.is_current && (
              <Card className="border-amber-400 bg-amber-50">
                <p className="text-sm font-medium text-amber-800">
                  Ce résultat ne correspond plus à la version actuelle de l'étude.
                </p>
                <p className="mt-1 text-sm text-amber-700">
                  Consultez-le à titre d'historique, ou relancez le calcul pour obtenir le résultat courant.
                </p>
              </Card>
            )}

            {(job || (result.requested_engine && result.requested_engine !== 'quick_solver')) && (
              <Card>
                <p className="text-sm text-ink-soft">
                  {ENERGYPLUS_STATUS_LABEL[
                    job?.energyplus_processing_status ?? result.energyplus_processing_status
                  ] ?? 'Statut EnergyPlus inconnu.'}
                </p>
              </Card>
            )}

            {rerunError && (
              <Card className="border-red-300 bg-red-50">
                <p className="text-sm text-red-700">{rerunError}</p>
              </Card>
            )}

            <Card>
              <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm text-ink-faint">Puissance de refroidissement recommandée</p>
                  <p className="mt-1 text-3xl font-semibold text-brand-700">
                    {(result.recommended_capacity_w / 1000).toFixed(2)} kW
                  </p>
                  <p className="mt-1 text-sm text-ink-soft">
                    {result.recommended_capacity_w.toFixed(0)} W · {result.recommended_capacity_btu_h.toFixed(0)} BTU/h
                    {result.commercial_capacity && (
                      <> · Palier commercial : {result.commercial_capacity.name}</>
                    )}
                  </p>
                </div>
                <div className="flex flex-col items-start gap-1 sm:items-end">
                  <Badge tone="brand">Scénario dimensionnant : {result.governing_scenario_code}</Badge>
                  <span className="text-sm text-ink-soft">
                    Confiance : {(result.confidence_score * 100).toFixed(0)} %
                  </span>
                  <span className="text-xs text-ink-faint">Moteur {result.engine} {result.engine_version}</span>
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatTile icon="🔥" label="Charge sensible" value={`${(result.sensible_load_w / 1000).toFixed(2)} kW`} />
              <StatTile icon="💧" label="Charge latente" value={`${(result.latent_load_w / 1000).toFixed(2)} kW`} />
              <StatTile icon="Σ" label="Charge totale" value={`${(result.total_load_w / 1000).toFixed(2)} kW`} />
              <StatTile icon="%" label="SHR" value={result.shr.toFixed(2)} />
            </div>

            <Card title="Répartition des charges (scénario dimensionnant)">
              <div className="flex flex-col divide-y divide-border">
                {result.breakdown
                  .filter((b) => b.total_w > 1)
                  .sort((a, b) => b.total_w - a.total_w)
                  .map((entry) => (
                    <div key={entry.component_code} className="flex items-center gap-3 py-2 text-sm">
                      <span className="w-48 shrink-0 text-ink">{entry.label}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted">
                        <div
                          className="h-full bg-brand-500"
                          style={{ width: `${Math.min(100, (entry.total_w / result.total_load_w) * 100)}%` }}
                        />
                      </div>
                      <span className="w-16 shrink-0 text-right text-ink-soft">{entry.total_w.toFixed(0)} W</span>
                    </div>
                  ))}
              </div>
            </Card>

            {result.solar_gain_by_facade.length > 0 && (
              <Card title="Apports solaires par façade">
                <div className="flex flex-col divide-y divide-border">
                  {[...result.solar_gain_by_facade]
                    .sort((a, b) => b.gain_w - a.gain_w)
                    .map((entry) => (
                      <div key={entry.facade} className="flex items-center gap-3 py-2 text-sm">
                        <span className="w-24 shrink-0 capitalize text-ink">{FACADE_LABELS_FR[entry.facade]}</span>
                        <span className="w-20 shrink-0 text-ink-faint">{entry.area_m2.toFixed(1)} m²</span>
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted">
                          <div
                            className="h-full bg-brand-500"
                            style={{
                              width: `${Math.min(
                                100,
                                (entry.gain_w / Math.max(1, result.solar_gain_by_facade[0]?.gain_w ?? 1)) * 100,
                              )}%`,
                            }}
                          />
                        </div>
                        <span className="w-16 shrink-0 text-right text-ink-soft">{entry.gain_w.toFixed(0)} W</span>
                      </div>
                    ))}
                </div>
                <p className="mt-3 text-xs text-ink-faint">
                  Décomposition informative de l'apport solaire vitrages déjà inclus dans « Répartition des charges »
                  — non additionnée en plus du total.
                </p>
              </Card>
            )}

            {result.warnings.length > 0 && (
              <Card title="Avertissements">
                <div className="flex flex-col gap-2">
                  {result.warnings.map((w) => (
                    <div key={w.code} className="flex items-start gap-2 text-sm">
                      <Badge tone={w.severity === 'warning' ? 'warn' : 'neutral'}>{w.code}</Badge>
                      <span className="text-ink-soft">{w.message}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {result.main_load_drivers.length > 0 && (
              <Card title="Facteurs principaux">
                <div className="flex flex-wrap gap-2">
                  {result.main_load_drivers.map((driver) => (
                    <Badge key={driver.code} tone="brand">
                      {driver.label} ({driver.percentage.toFixed(0)} %)
                    </Badge>
                  ))}
                </div>
              </Card>
            )}

            <div className="flex justify-end gap-3">
              <Button variant="secondary" disabled={rerunning} onClick={() => void handleRerun()}>
                {rerunning ? 'Relance en cours…' : 'Relancer le calcul'}
              </Button>
              <Link to={`/cooling/studies/${studyId}/equipment-selection`}>
                <Button>Sélectionner un équipement →</Button>
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
