import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { AppHeader } from '../components/layout/AppHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useStudyStore } from '../store/studyStore';

export function StudiesListPage() {
  const studiesById = useStudyStore((state) => state.studies);
  const studies = useMemo(() => Object.values(studiesById), [studiesById]);

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

        {studies.length === 0 ? (
          <Card>
            <p className="text-sm text-ink-soft">
              Aucune étude pour le moment. Créez votre première étude pour dimensionner le besoin de refroidissement
              d'un GreenCube.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {studies.map((study) => (
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
                  </p>
                  <p className="mt-3 text-xs text-ink-soft">
                    {study.completedSteps.length} / 7 étapes complétées
                  </p>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
