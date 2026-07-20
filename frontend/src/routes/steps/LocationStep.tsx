import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { EnvironmentType, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';
import { useEffect, useRef, useState } from 'react';
import { fetchGeoContext, searchAddress, type GeoSearchResult } from '../../api/geo';

const ENVIRONMENT_OPTIONS: { code: EnvironmentType; label: string }[] = [
  { code: 'dense_urban', label: 'Centre-ville dense' },
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
  const [suggestions, setSuggestions] = useState<GeoSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (address.trim().length < 3) {
      setSuggestions([]);
      return;
    }
    const controller = new AbortController();
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      setGeoError(null);
      try {
        const results = await searchAddress(address, controller.signal);
        setSuggestions(results);
      } catch (err) {
        if (!controller.signal.aborted) {
          setGeoError("Recherche d'adresse indisponible pour le moment.");
        }
      } finally {
        setSearching(false);
      }
    }, 400);
    return () => controller.abort();
  }, [address]);

  function applyLocation(latitude: number, longitude: number, extra: Partial<StudyDraft['location']> = {}) {
    updateStudy(studyId, {
      location: { ...study.location, ...extra, latitude, longitude },
    });
  }

  async function refineWithGeoContext(latitude: number, longitude: number) {
    try {
      const context = await fetchGeoContext(latitude, longitude);
      updateStudy(studyId, {
        location: {
          ...study.location,
          latitude,
          longitude,
          altitudeM: context.altitude_m ?? study.location.altitudeM,
          timezone: context.timezone ?? study.location.timezone,
        },
      });
    } catch {
      // Keep the coordinates already applied; altitude/timezone refinement is best-effort.
    }
  }

  function selectSuggestion(result: GeoSearchResult) {
    setAddress(result.label);
    setSuggestions([]);
    applyLocation(result.latitude, result.longitude, {
      address: result.label,
      city: result.city,
      altitudeM: result.altitude_m,
      timezone: result.timezone,
    });
    void refineWithGeoContext(result.latitude, result.longitude);
  }

  function useMyPosition() {
    setGeoError(null);
    if (!navigator.geolocation) {
      setGeoError("La géolocalisation n'est pas disponible dans ce navigateur.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        applyLocation(latitude, longitude);
        void refineWithGeoContext(latitude, longitude).finally(() => setLocating(false));
      },
      () => {
        setGeoError('Position refusée ou indisponible.');
        setLocating(false);
      },
      { enableHighAccuracy: false, timeout: 8000 },
    );
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
              <div className="relative">
                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Adresse, commune ou coordonnées GPS"
                  className="w-full rounded-lg border border-border px-4 py-2.5 text-sm outline-none focus:border-brand-500"
                />
                {searching && (
                  <div className="absolute right-3 top-2.5 text-xs text-ink-faint">Recherche…</div>
                )}
                {suggestions.length > 0 && (
                  <ul className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-surface shadow-lg">
                    {suggestions.map((s, i) => (
                      <li key={`${s.latitude}-${s.longitude}-${i}`}>
                        <button
                          type="button"
                          onClick={() => selectSuggestion(s)}
                          className="block w-full px-4 py-2 text-left text-sm hover:bg-surface-muted"
                        >
                          {s.label}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <Button variant="secondary" onClick={useMyPosition} disabled={locating} className="w-fit">
                {locating ? 'Localisation…' : '📍 Utiliser ma position'}
              </Button>
              {geoError && <p className="text-xs text-red-600">{geoError}</p>}
              <div className="grid grid-cols-3 gap-3 rounded-xl border border-border bg-surface-muted p-4 text-sm">
                <div>
                  <div className="text-ink-faint">Latitude</div>
                  <div className="font-medium text-ink">
                    {study.location.latitude != null ? `${study.location.latitude.toFixed(4)} °N` : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-ink-faint">Longitude</div>
                  <div className="font-medium text-ink">
                    {study.location.longitude != null ? `${study.location.longitude.toFixed(4)} °E` : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-ink-faint">Altitude</div>
                  <div className="font-medium text-ink">
                    {study.location.altitudeM != null ? `${study.location.altitudeM} m` : '—'}
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
            <MiniStat label="Fuseau horaire" value={study.location.timezone ?? '—'} />
            <MiniStat label="Commune" value={study.location.city ?? '—'} />
            <MiniStat label="Altitude estimée" value={study.location.altitudeM != null ? `${study.location.altitudeM} m` : '—'} />
            <MiniStat label="Source climatique" value="Open-Meteo (géocodage + altitude)" />
          </div>
          <div className="flex flex-col gap-3 border-t border-border p-6">
            <p className="text-sm text-ink-soft">
              Les scénarios climatiques détaillés (été de référence, forte chaleur, canicule) sont calculés à
              l'étape de calcul à partir de ces coordonnées.
            </p>
            <div className="flex gap-3">
              <Button onClick={confirm} disabled={study.location.latitude == null}>
                Confirmer
              </Button>
              <Button variant="secondary" onClick={() => setAddress('')}>
                Modifier la localisation
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <WizardFooter nextSteps={defaultNextSteps} onContinue={confirm} continueDisabled={study.location.latitude == null} />
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
