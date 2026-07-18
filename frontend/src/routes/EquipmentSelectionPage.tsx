import { useEffect, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useStudyStore } from '../store/studyStore';
import { getEquipmentRecommendations, postEquipmentSelection, type EquipmentRecommendation } from '../api/study';
import { ApiError } from '../api/client';

const STATUS_LABELS: Record<string, string> = {
  recommended: 'Recommandé',
  strong_alternative: 'Bonne alternative',
  compatible: 'Compatible',
  compatible_with_conditions: 'Compatible sous conditions',
  not_recommended: 'Non recommandé',
  incompatible: 'Incompatible',
};

const STATUS_TONE: Record<string, 'brand' | 'warn' | 'neutral'> = {
  recommended: 'brand',
  strong_alternative: 'brand',
  compatible: 'neutral',
  compatible_with_conditions: 'warn',
  not_recommended: 'warn',
  incompatible: 'warn',
};

export function EquipmentSelectionPage() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  const updateStudy = useStudyStore((state) => state.updateStudy);

  const [recommendations, setRecommendations] = useState<EquipmentRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectingId, setSelectingId] = useState<number | null>(null);

  useEffect(() => {
    if (!study?.backendId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    getEquipmentRecommendations(study.backendId)
      .then((data) => {
        if (!cancelled) setRecommendations(data.sort((a, b) => (a.oversizing_ratio ?? 99) - (b.oversizing_ratio ?? 99)));
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Aucun résultat disponible : complétez d'abord la vérification et le calcul de puissance.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [study?.backendId]);

  async function select(productId: number) {
    if (!study?.backendId) return;
    setSelectingId(productId);
    try {
      await postEquipmentSelection(study.backendId, productId);
      updateStudy(study.id, { selectedEquipmentProductId: String(productId), status: 'calculated' });
    } finally {
      setSelectingId(null);
    }
  }

  if (!studyId || !study) {
    return <Navigate to="/cooling/studies" replace />;
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

        {loading ? (
          <Card>
            <p className="text-sm text-ink-soft">Chargement des recommandations…</p>
          </Card>
        ) : error || !study.backendId ? (
          <Card>
            <p className="text-sm text-ink-soft">
              {error ?? "Aucun résultat disponible : complétez d'abord la vérification et le calcul de puissance."}
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {recommendations.map(({ product, status, reasons }) => {
              const selected = study.selectedEquipmentProductId === String(product.id);
              const isIncompatible = status === 'incompatible';
              return (
                <Card key={product.id} className={selected ? 'border-brand-500' : undefined}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-ink">{product.name}</h3>
                      <p className="mt-1 text-xs text-ink-faint">{product.type}</p>
                    </div>
                    <Badge tone={STATUS_TONE[status] ?? 'neutral'}>{STATUS_LABELS[status] ?? status}</Badge>
                  </div>

                  <dl className="mt-4 grid grid-cols-2 gap-y-2 text-sm">
                    <dt className="text-ink-faint">Capacité nominale</dt>
                    <dd className="text-right text-ink">{((product.nominal_capacity_w ?? 0) / 1000).toFixed(2)} kW</dd>
                    <dt className="text-ink-faint">Capacité à 45 °C</dt>
                    <dd className="text-right text-ink">{((product.capacity_at_45c_w ?? 0) / 1000).toFixed(2)} kW</dd>
                    <dt className="text-ink-faint">EER / SEER</dt>
                    <dd className="text-right text-ink">{product.eer} / {product.seer}</dd>
                    <dt className="text-ink-faint">SHR</dt>
                    <dd className="text-right text-ink">{product.shr}</dd>
                    <dt className="text-ink-faint">Bruit</dt>
                    <dd className="text-right text-ink">{product.noise_db} dB</dd>
                    <dt className="text-ink-faint">Alimentation</dt>
                    <dd className="text-right text-ink">{product.power_supply}</dd>
                    <dt className="text-ink-faint">Prix indicatif</dt>
                    <dd className="text-right text-ink">{(product.list_price ?? 0).toLocaleString('fr-FR')} €</dd>
                  </dl>

                  <ul className="mt-3 flex flex-col gap-1 text-xs text-ink-soft">
                    {reasons.map((r) => (
                      <li key={r}>• {r}</li>
                    ))}
                  </ul>

                  <Button
                    className="mt-4 w-full"
                    variant={selected ? 'primary' : 'secondary'}
                    disabled={isIncompatible || selectingId === product.id}
                    onClick={() => void select(product.id)}
                  >
                    {selected ? 'Sélectionné ✓' : isIncompatible ? 'Incompatible' : selectingId === product.id ? 'Sélection…' : 'Sélectionner'}
                  </Button>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
