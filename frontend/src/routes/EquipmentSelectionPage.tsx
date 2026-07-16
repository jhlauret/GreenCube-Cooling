import { useMemo } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useStudyStore } from '../store/studyStore';
import { runMercure } from '../mercure/engine';
import { mapStudyToMercureInput } from '../mercure/mapStudyToInput';
import { CATALOG_PRODUCTS } from '../api/mockCatalog';
import { assessCompatibility, COMPATIBILITY_LABELS, COMPATIBILITY_TONE } from '../equipment/compatibility';

export function EquipmentSelectionPage() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  const updateStudy = useStudyStore((state) => state.updateStudy);

  const governing = useMemo(() => {
    if (!study) return null;
    try {
      const result = runMercure(mapStudyToMercureInput(study));
      return result.scenarioResults.find((s) => s.scenarioCode === result.governingScenarioCode) ?? null;
    } catch {
      return null;
    }
  }, [study]);

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
  }

  const assessments = governing
    ? CATALOG_PRODUCTS.map((product) => ({ product, assessment: assessCompatibility(product, governing) })).sort(
        (a, b) => a.assessment.oversizingRatio - b.assessment.oversizingRatio,
      )
    : [];

  function select(productId: string) {
    updateStudy(studyId!, { selectedEquipmentProductId: productId, status: 'calculated' });
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader />
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-ink">Sélection d'équipement — {study.name}</h1>
          <Link to={`/cooling/studies/${studyId}/results`} className="text-sm text-brand-700 hover:underline">
            ← Revenir aux résultats
          </Link>
        </div>

        {!governing ? (
          <Card>
            <p className="text-sm text-ink-soft">
              Aucun résultat disponible : complétez d'abord la vérification et le calcul de puissance.
            </p>
          </Card>
        ) : (
          <div className="flex flex-col gap-4">
            <Card>
              <p className="text-sm text-ink-soft">
                Puissance recommandée : <span className="font-semibold text-ink">{(governing.recommendedLoadW / 1000).toFixed(2)} kW</span> ·
                SHR : <span className="font-semibold text-ink">{governing.shr.toFixed(2)}</span>
              </p>
            </Card>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {assessments.map(({ product, assessment }) => {
                const selected = study.selectedEquipmentProductId === product.id;
                const isIncompatible = assessment.status === 'incompatible';
                return (
                  <Card key={product.id} className={selected ? 'border-brand-500' : undefined}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-semibold text-ink">{product.name}</h3>
                        <p className="mt-1 text-xs text-ink-faint">{product.type}</p>
                      </div>
                      <Badge tone={COMPATIBILITY_TONE[assessment.status]}>{COMPATIBILITY_LABELS[assessment.status]}</Badge>
                    </div>

                    <dl className="mt-4 grid grid-cols-2 gap-y-2 text-sm">
                      <dt className="text-ink-faint">Capacité nominale</dt>
                      <dd className="text-right text-ink">{(product.nominalCapacityW / 1000).toFixed(2)} kW</dd>
                      <dt className="text-ink-faint">Capacité à 45 °C</dt>
                      <dd className="text-right text-ink">{(product.capacityAt45CW / 1000).toFixed(2)} kW</dd>
                      <dt className="text-ink-faint">EER / SEER</dt>
                      <dd className="text-right text-ink">{product.eer} / {product.seer}</dd>
                      <dt className="text-ink-faint">SHR</dt>
                      <dd className="text-right text-ink">{product.shr}</dd>
                      <dt className="text-ink-faint">Bruit</dt>
                      <dd className="text-right text-ink">{product.noiseDb} dB</dd>
                      <dt className="text-ink-faint">Alimentation</dt>
                      <dd className="text-right text-ink">{product.powerSupply}</dd>
                      <dt className="text-ink-faint">Prix indicatif</dt>
                      <dd className="text-right text-ink">{product.priceEur.toLocaleString('fr-FR')} €</dd>
                    </dl>

                    <ul className="mt-3 flex flex-col gap-1 text-xs text-ink-soft">
                      {assessment.reasons.map((r) => (
                        <li key={r}>• {r}</li>
                      ))}
                    </ul>

                    <Button
                      className="mt-4 w-full"
                      variant={selected ? 'primary' : 'secondary'}
                      disabled={isIncompatible}
                      onClick={() => select(product.id)}
                    >
                      {selected ? 'Sélectionné ✓' : isIncompatible ? 'Incompatible' : 'Sélectionner'}
                    </Button>
                  </Card>
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
