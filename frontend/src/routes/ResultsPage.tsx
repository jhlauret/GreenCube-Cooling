import { useEffect, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { StatTile } from '../components/ui/StatTile';
import { useStudyStore } from '../store/studyStore';
import { syncStudyToBackend } from '../sync/syncStudy';
import { calculate, getStudyResults, type BackendResult } from '../api/study';
import { ApiError } from '../api/client';

export function ResultsPage() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  const updateStudy = useStudyStore((state) => state.updateStudy);

  const [result, setResult] = useState<BackendResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!study) return;
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const backendId = await syncStudyToBackend(study!, (id) => updateStudy(study!.id, { backendId: id }));
        const computed = await calculate(backendId);
        if (!cancelled) setResult(computed);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Le calcul n'a pas pu être exécuté : vérifiez la localisation, le modèle et l'orientation.",
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
  }, [study?.id]);

  async function refreshFromLatest() {
    if (!study?.backendId) return;
    const results = await getStudyResults(study.backendId);
    if (results.length > 0) setResult(results[0]);
  }

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader />
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

            <div className="flex justify-end">
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
