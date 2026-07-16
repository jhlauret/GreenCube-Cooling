import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { EnvironmentType, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';
import { useState } from 'react';

const ENVIRONMENT_OPTIONS: { code: EnvironmentType; label: string }[] = [
  { code: 'urban_dense', label: 'Centre-ville dense' },
  { code: 'suburban', label: 'Périurbain' },
  { code: 'rural', label: 'Campagne' },
  { code: 'mountain', label: 'Montagne' },
  { code: 'coastal', label: 'Bord de mer' },
  { code: 'industrial', label: 'Zone industrielle' },
];

const AUTO_DATA = [
  { icon: '🌡️', label: 'Historique de températures' },
  { icon: '💧', label: 'Humidité' },
  { icon: '☀️', label: 'Rayonnement solaire' },
  { icon: '🌬️', label: 'Vent' },
  { icon: '🌙', label: 'Nuits tropicales' },
  { icon: '🔥', label: 'Vagues de chaleur' },
  { icon: '📈', label: 'Projections climatiques' },
];

export function LocationStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext } = useWizardNav('location');
  const [address, setAddress] = useState(study.location.address);

  function detectClimate() {
    updateStudy(studyId, {
      location: {
        ...study.location,
        address,
        latitude: 46.2263,
        longitude: 7.1231,
        altitudeM: 1200,
      },
    });
  }

  function setEnvironment(env: EnvironmentType) {
    updateStudy(studyId, { location: { ...study.location, environmentType: env } });
  }

  function confirm() {
    updateStudy(studyId, { location: { ...study.location, climateConfirmed: true } });
    goToNext();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <Card title="Où sera installé votre GreenCube ?">
            <div className="flex flex-col gap-3">
              <input
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Adresse, commune ou coordonnées GPS"
                className="rounded-lg border border-border px-4 py-2.5 text-sm outline-none focus:border-brand-500"
              />
              <Button variant="secondary" onClick={detectClimate} className="w-fit">
                📍 Utiliser ma position
              </Button>
              <div className="grid grid-cols-3 gap-3 rounded-xl border border-border bg-surface-muted p-4 text-sm">
                <div>
                  <div className="text-ink-faint">Latitude</div>
                  <div className="font-medium text-ink">
                    {study.location.latitude ? `${study.location.latitude.toFixed(4)} °N` : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-ink-faint">Longitude</div>
                  <div className="font-medium text-ink">
                    {study.location.longitude ? `${study.location.longitude.toFixed(4)} °E` : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-ink-faint">Altitude</div>
                  <div className="font-medium text-ink">
                    {study.location.altitudeM ? `${study.location.altitudeM} m` : '—'}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Type d'environnement">
            <div className="flex flex-wrap gap-2">
              {ENVIRONMENT_OPTIONS.map((opt) => (
                <button
                  key={opt.code}
                  onClick={() => setEnvironment(opt.code)}
                  className={
                    'rounded-full border px-4 py-2 text-sm transition-colors ' +
                    (study.location.environmentType === opt.code
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-border text-ink-soft hover:border-brand-300')
                  }
                >
                  {opt.label}
                  {study.location.environmentType === opt.code && ' ✓'}
                </button>
              ))}
            </div>
          </Card>

          <Card title="Données récupérées automatiquement">
            <div className="grid grid-cols-2 gap-3 text-sm text-ink-soft">
              {AUTO_DATA.map((d) => (
                <div key={d.label} className="flex items-center gap-2">
                  <span aria-hidden>{d.icon}</span>
                  {d.label}
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card title="Contexte climatique détecté" padded={false}>
          <div className="flex h-56 items-center justify-center border-b border-border bg-surface-muted text-sm text-ink-faint">
            Carte (aperçu non disponible hors ligne)
          </div>
          <div className="grid grid-cols-2 gap-3 p-6 sm:grid-cols-3">
            <MiniStat label="Température de référence" value={study.location.latitude ? '37 °C' : '—'} />
            <MiniStat label="Scénario canicule renforcée" value={study.location.latitude ? '42 °C' : '—'} />
            <MiniStat label="Nuits tropicales récentes" value={study.location.latitude ? 'Fréquentes' : '—'} />
            <MiniStat label="Altitude estimée" value={study.location.altitudeM ? `${study.location.altitudeM} m` : '—'} />
            <MiniStat label="Source climatique" value="API historique + signal récent" />
          </div>
          <div className="flex flex-col gap-3 border-t border-border p-6">
            <p className="text-sm text-ink-soft">Les données climatiques correspondent-elles bien au site ?</p>
            <div className="flex gap-3">
              <Button onClick={confirm} disabled={!study.location.latitude}>
                Confirmer
              </Button>
              <Button variant="secondary">Modifier la localisation</Button>
            </div>
          </div>
        </Card>
      </div>

      <WizardFooter nextSteps={defaultNextSteps} onContinue={confirm} continueDisabled={!study.location.latitude} />
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border p-3 text-center">
      <div className="text-xs text-ink-faint">{label}</div>
      <div className="mt-1 text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}
