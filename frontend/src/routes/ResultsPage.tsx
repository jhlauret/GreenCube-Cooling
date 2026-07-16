import { useMemo } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { StatTile } from '../components/ui/StatTile';
import { useStudyStore } from '../store/studyStore';
import { runMercure } from '../mercure/engine';
import { mapStudyToMercureInput } from '../mercure/mapStudyToInput';
import type { MercureWarning } from '../mercure/types';

function dedupeWarnings(warnings: MercureWarning[]): MercureWarning[] {
  return Array.from(new Map(warnings.map((w) => [w.code, w])).values());
}

export function ResultsPage() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));

  const result = useMemo(() => {
    if (!study) return null;
    try {
      return runMercure(mapStudyToMercureInput(study));
    } catch {
      return null;
    }
  }, [study]);

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
  }

  const governing = result?.scenarioResults.find((s) => s.scenarioCode === result.governingScenarioCode);

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

        {!result || !governing ? (
          <Card>
            <p className="text-sm text-ink-soft">
              Le calcul n'a pas pu être exécuté : complétez d'abord la localisation, le modèle et l'orientation.
            </p>
          </Card>
        ) : (
          <div className="flex flex-col gap-4">
            <Card>
              <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm text-ink-faint">Puissance de refroidissement recommandée</p>
                  <p className="mt-1 text-3xl font-semibold text-brand-700">
                    {(result.recommendedCapacityW / 1000).toFixed(2)} kW
                  </p>
                  <p className="mt-1 text-sm text-ink-soft">
                    {result.recommendedCapacityW.toFixed(0)} W · {result.recommendedCapacityBtuH.toFixed(0)} BTU/h
                  </p>
                </div>
                <div className="flex flex-col items-start gap-1 sm:items-end">
                  <Badge tone="brand">Scénario dimensionnant : {governing.scenarioCode}</Badge>
                  <span className="text-sm text-ink-soft">
                    Confiance : {(result.confidenceScore * 100).toFixed(0)} %
                  </span>
                  <span className="text-xs text-ink-faint">Moteur MERCURE {result.engineVersion}</span>
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatTile icon="🔥" label="Charge sensible" value={`${(governing.sensibleLoadW / 1000).toFixed(2)} kW`} />
              <StatTile icon="💧" label="Charge latente" value={`${(governing.latentLoadW / 1000).toFixed(2)} kW`} />
              <StatTile icon="Σ" label="Charge totale" value={`${(governing.totalLoadW / 1000).toFixed(2)} kW`} />
              <StatTile icon="%" label="SHR" value={governing.shr.toFixed(2)} />
            </div>

            <Card title="Répartition des charges (scénario dimensionnant)">
              <div className="flex flex-col divide-y divide-border">
                {governing.breakdown
                  .filter((b) => b.totalW > 1)
                  .sort((a, b) => b.totalW - a.totalW)
                  .map((entry) => (
                    <div key={entry.componentCode} className="flex items-center gap-3 py-2 text-sm">
                      <span className="w-48 shrink-0 text-ink">{entry.label}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted">
                        <div
                          className="h-full bg-brand-500"
                          style={{ width: `${Math.min(100, (entry.totalW / governing.totalLoadW) * 100)}%` }}
                        />
                      </div>
                      <span className="w-16 shrink-0 text-right text-ink-soft">{entry.totalW.toFixed(0)} W</span>
                    </div>
                  ))}
              </div>
            </Card>

            <Card title="Comparaison des scénarios">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[480px] text-sm">
                  <thead>
                    <tr className="text-left text-ink-faint">
                      <th className="pb-2 font-medium">Scénario</th>
                      <th className="pb-2 font-medium">Sensible</th>
                      <th className="pb-2 font-medium">Latent</th>
                      <th className="pb-2 font-medium">Total</th>
                      <th className="pb-2 font-medium">Recommandé</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {result.scenarioResults.map((s) => (
                      <tr key={s.scenarioCode} className={s.scenarioCode === governing.scenarioCode ? 'font-semibold text-ink' : 'text-ink-soft'}>
                        <td className="py-2">{s.scenarioCode}</td>
                        <td className="py-2">{(s.sensibleLoadW / 1000).toFixed(2)} kW</td>
                        <td className="py-2">{(s.latentLoadW / 1000).toFixed(2)} kW</td>
                        <td className="py-2">{(s.totalLoadW / 1000).toFixed(2)} kW</td>
                        <td className="py-2">{(s.recommendedLoadW / 1000).toFixed(2)} kW</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {result.warnings.length > 0 && (
              <Card title="Avertissements">
                <div className="flex flex-col gap-2">
                  {dedupeWarnings(result.warnings).map((w) => (
                    <div key={w.code} className="flex items-start gap-2 text-sm">
                      <Badge tone={w.level === 'warning' ? 'warn' : 'neutral'}>{w.code}</Badge>
                      <span className="text-ink-soft">{w.message}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            <Card title="Facteurs principaux">
              <div className="flex flex-wrap gap-2">
                {result.mainLoadDrivers.map((driver) => (
                  <Badge key={driver} tone="brand">
                    {driver}
                  </Badge>
                ))}
              </div>
            </Card>

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
