import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useStudyStore } from '../store/studyStore';
import { listStudies, type BackendStudySummary } from '../api/study';
import { loadStudyFromBackend } from '../sync/syncStudy';
import { ApiError } from '../api/client';

/**
 * Odoo is the source of truth for which studies exist (audit P0-04):
 * this page always fetches GET /studies and shows every backend study,
 * even ones with no local draft (created elsewhere, or after clearing
 * browser storage). Opening a backend-only study imports it into a local
 * draft on demand via loadStudyFromBackend, rather than requiring the
 * whole wizard to be re-keyed off backend ids.
 */
export function StudiesListPage() {
  const studiesById = useStudyStore((state) => state.studies);
  const localStudies = useMemo(() => Object.values(studiesById), [studiesById]);
  const findByBackendId = useStudyStore((state) => state.findByBackendId);
  const createStudy = useStudyStore((state) => state.createStudy);
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const navigate = useNavigate();

  const [backendStudies, setBackendStudies] = useState<BackendStudySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importingId, setImportingId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    listStudies()
      .then((data) => {
        if (!cancelled) setBackendStudies(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Impossible de contacter l'API GreenCube Cooling.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const backendOnlyStudies = backendStudies.filter((bs) => !findByBackendId(bs.id));

  async function importStudy(backendId: number) {
    setImportingId(backendId);
    try {
      const patch = await loadStudyFromBackend(backendId);
      const localId = createStudy(patch.name ?? `Étude #${backendId}`);
      updateStudy(localId, patch);
      navigate(`/cooling/studies/${localId}/location`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'importer cette étude depuis Odoo.");
    } finally {
      setImportingId(null);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface-muted">
      <AppHeader />
      <main className="mx-auto w-full max-w-5xl flex-1 px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-ink">Vos études GreenCube Cooling</h1>
          <Link to="/cooling/studies/new">
            <Button>+ Nouvelle étude</Button>
          </Link>
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        {localStudies.length === 0 && backendOnlyStudies.length === 0 ? (
          <Card>
            <p className="text-sm text-ink-soft">
              {loading
                ? 'Chargement des études depuis Odoo…'
                : "Aucune étude pour le moment. Créez votre première étude pour dimensionner le besoin de refroidissement d'un GreenCube."}
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {localStudies.map((study) => (
              <Link key={study.id} to={`/cooling/studies/${study.id}/location`}>
                <Card className="transition-colors hover:border-brand-400">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-ink">{study.name}</h2>
                    <Badge tone={study.status === 'calculated' ? 'brand' : 'neutral'}>
                      {study.status === 'calculated' ? 'Calculée' : study.status === 'ready' ? 'Prête' : 'Brouillon'}
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-ink-faint">
                    Mise à jour le {new Date(study.updatedAt).toLocaleDateString('fr-FR')}
                    {study.backendId ? ' · synchronisé avec Odoo' : ' · brouillon local uniquement'}
                  </p>
                  <p className="mt-3 text-xs text-ink-soft">
                    {study.completedSteps.length} / 7 étapes complétées
                  </p>
                </Card>
              </Link>
            ))}

            {backendOnlyStudies.map((study) => (
              <Card key={`backend-${study.id}`} className="border-dashed">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-ink">{study.name}</h2>
                  <Badge tone="neutral">Odoo — pas de brouillon local</Badge>
                </div>
                <p className="mt-2 text-xs text-ink-faint">
                  {study.location.address || 'Adresse non renseignée'}
                  {study.updated_at ? ` · mise à jour le ${new Date(study.updated_at).toLocaleDateString('fr-FR')}` : ''}
                </p>
                <Button
                  variant="secondary"
                  className="mt-3"
                  disabled={importingId === study.id}
                  onClick={() => void importStudy(study.id)}
                >
                  {importingId === study.id ? 'Import en cours…' : 'Ouvrir dans le configurateur →'}
                </Button>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
