import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { ClimateScenarioData, EnvironmentType, StudyDraft } from '../../types/study';
import { defaultNextSteps } from './defaultNextSteps';
import { useEffect, useRef, useState } from 'react';
import { confirmLocation, fetchGeoContext, searchAddress, type GeoSearchResult } from '../../api/geo';
import type { LocationPrecision, LocationProvenance } from '../../types/study';

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
  // Historical percentiles only (GC-COOLING-04): this service derives its
  // three dimensioning scenarios from ~10 years of observed daily weather
  // (Open-Meteo/ERA5 reanalysis), never from a forward-looking climate
  // projection model. Do not relabel this "Projections climatiques" again
  // without also wiring a real prospective-model provider behind its own
  // feature flag — see services/climate.py's DATASET_TYPE_HISTORICAL_OBSERVED.
  { icon: '📈', label: 'Historique multi-année (10 ans)' },
];

const SCENARIO_LABELS: Record<ClimateScenarioData['scenarioType'], string> = {
  reference_summer: 'Été de référence',
  hot_weather: 'Forte chaleur',
  prolonged_heatwave: 'Canicule prolongée',
};

// Dataset types/provenances the backend flags as not being a real,
// confidently-sourced measurement (services/climate.py + climate_scenario.py):
// the UI must require an explicit acknowledgement before letting the user
// proceed on these (README_GC-COOLING-07 §6 "Exiger une confirmation
// explicite des données estimées ou dégradées.").
const DEGRADED_PROVENANCES = new Set(['estimated_reference', 'estimated_manual', 'missing_fallback']);

function isDegradedScenario(s: ClimateScenarioData): boolean {
  return DEGRADED_PROVENANCES.has(s.provenance) || !s.datasetType;
}

function formatPeriod(scenario: ClimateScenarioData): string | null {
  if (scenario.dataStart && scenario.dataEnd) {
    return `${scenario.dataStart} → ${scenario.dataEnd}`;
  }
  return scenario.referenceDate;
}

function parseCoordinateInput(raw: string): number | null {
  // README §12 "prévoir point ou virgule décimale".
  const normalized = raw.trim().replace(',', '.');
  if (normalized === '') return null;
  const value = Number(normalized);
  return Number.isFinite(value) ? value : NaN;
}

export function LocationStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext } = useWizardNav('location');
  const [address, setAddress] = useState(study.location.address);
  const [suggestions, setSuggestions] = useState<GeoSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [retryToken, setRetryToken] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Tracks how the current coordinates were obtained, so confirm() can pass
  // an honest provenance to POST /confirm-location instead of guessing
  // (GC-COOLING-03: "conserver la provenance de chaque champ"). Defaults to
  // 'manual' since simply typing/editing the address field without picking
  // a suggestion never goes through the geocoder.
  const [locationProvenance, setLocationProvenance] = useState<LocationProvenance>(
    study.location.locationProvenance ?? 'manual',
  );
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [acknowledgedDegraded, setAcknowledgedDegraded] = useState(false);

  // Manual coordinates entry (README §12) — kept as free-text so the user
  // can type a comma or a dot decimal separator; validated on submit only.
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');
  const [manualError, setManualError] = useState<string | null>(null);

  // Manual altitude correction (README §17): the provider-fetched value is
  // kept in study.location.altitudeM; this only tracks the user's override
  // text so the difference stays visible until applied.
  const [altitudeDraft, setAltitudeDraft] = useState('');
  const [altitudeError, setAltitudeError] = useState<string | null>(null);

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
      } catch {
        if (!controller.signal.aborted) {
          setGeoError("Recherche d'adresse indisponible pour le moment.");
        }
      } finally {
        setSearching(false);
      }
    }, 400);
    return () => controller.abort();
  }, [address, retryToken]);

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
    setLocationProvenance('geocoded');
    setAcknowledgedDegraded(false);
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
        // The browser's own position is still treated as a fresh, unverified
        // input (README §2.4 "traiter cette position comme une saisie
        // manuelle ; revalider les coordonnées"): applyLocation()/
        // refineWithGeoContext() below re-derive altitude/timezone from the
        // backend rather than trusting position.coords.altitude.
        const { latitude, longitude } = position.coords;
        setLocationProvenance('browser');
        setAcknowledgedDegraded(false);
        applyLocation(latitude, longitude);
        void refineWithGeoContext(latitude, longitude).finally(() => setLocating(false));
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          setGeoError('Position refusée : autorisez la géolocalisation dans votre navigateur pour continuer.');
        } else if (err.code === err.TIMEOUT) {
          setGeoError('La localisation a expiré. Réessayez ou saisissez une adresse.');
        } else {
          setGeoError('Position indisponible pour le moment.');
        }
        setLocating(false);
      },
      { enableHighAccuracy: false, timeout: 8000 },
    );
  }

  function applyManualCoordinates() {
    setManualError(null);
    const lat = parseCoordinateInput(manualLat);
    const lon = parseCoordinateInput(manualLon);
    if (lat === null || lon === null) {
      setManualError('Renseignez une latitude et une longitude.');
      return;
    }
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      setManualError('Latitude et longitude doivent être des nombres (point ou virgule décimale).');
      return;
    }
    if (lat < -90 || lat > 90) {
      setManualError('La latitude doit être comprise entre -90 et 90.');
      return;
    }
    if (lon < -180 || lon > 180) {
      setManualError('La longitude doit être comprise entre -180 et 180.');
      return;
    }
    setLocationProvenance('manual');
    setAcknowledgedDegraded(false);
    applyLocation(lat, lon);
    void refineWithGeoContext(lat, lon);
  }

  function applyManualAltitude() {
    setAltitudeError(null);
    const value = parseCoordinateInput(altitudeDraft);
    if (value === null) {
      setAltitudeError('Renseignez une altitude.');
      return;
    }
    if (Number.isNaN(value)) {
      setAltitudeError('Altitude invalide.');
      return;
    }
    if (value < -500 || value > 9000) {
      setAltitudeError("L'altitude doit être comprise entre -500 m et 9000 m.");
      return;
    }
    updateStudy(studyId, { location: { ...study.location, altitudeM: value } });
    setAltitudeDraft('');
  }

  function setEnvironment(env: EnvironmentType) {
    updateStudy(studyId, { location: { ...study.location, environmentType: env } });
  }

  const hasDegradedData =
    locationProvenance === 'manual' ||
    study.location.timezone == null ||
    study.location.altitudeM == null ||
    study.location.climateScenarios.some(isDegradedScenario);
  const canConfirm =
    study.location.latitude != null && study.location.longitude != null && (!hasDegradedData || acknowledgedDegraded);

  async function confirm() {
    if (study.location.latitude == null || study.location.longitude == null) return;
    if (hasDegradedData && !acknowledgedDegraded) return;
    setConfirmError(null);

    const provider =
      locationProvenance === 'geocoded' ? 'open-meteo' : locationProvenance === 'browser' ? 'browser-geolocation' : null;
    const precision: LocationPrecision =
      locationProvenance === 'geocoded' ? 'locality' : locationProvenance === 'browser' ? 'exact' : 'unknown';

    // POST /confirm-location is the only call allowed to set
    // climate_confirmed=true server-side and record provenance/precision
    // (GC-COOLING-03 §16). If the study has not reached the backend yet
    // (backendId still null — autosave hasn't created it) or the call
    // fails, the wizard still advances on the local draft: the next
    // autosave PATCH will persist lat/lon/climate_confirmed as before, it
    // will simply be missing the provenance metadata until the user
    // revisits this step once the study exists server-side.
    if (study.backendId) {
      setConfirming(true);
      try {
        await confirmLocation(study.backendId, {
          address: study.location.address || null,
          city: study.location.city,
          latitude: study.location.latitude,
          longitude: study.location.longitude,
          altitude_m: study.location.altitudeM,
          timezone: study.location.timezone,
          environment_type: study.location.environmentType,
          provenance: locationProvenance,
          provider,
          precision,
          source: study.location.address
            ? { display_name: study.location.address, city: study.location.city ?? undefined }
            : undefined,
        });
      } catch {
        setConfirmError(
          "La confirmation n'a pas pu être enregistrée côté serveur pour le moment ; elle sera renvoyée automatiquement.",
        );
      } finally {
        setConfirming(false);
      }
    }

    updateStudy(studyId, {
      location: {
        ...study.location,
        climateConfirmed: true,
        locationProvenance,
        locationProvider: provider,
        locationPrecision: precision,
      },
    });
    goToNext();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <Card title="Où sera installé votre GreenCube ?">
            <div className="flex flex-col gap-3">
              <div className="relative">
                <label htmlFor="location-search" className="sr-only">
                  Adresse, commune ou coordonnées GPS
                </label>
                <input
                  id="location-search"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Adresse, commune ou coordonnées GPS"
                  className="w-full rounded-lg border border-border px-4 py-2.5 text-sm outline-none focus:border-brand-500"
                  aria-describedby={geoError ? 'location-search-error' : undefined}
                />
                {searching && (
                  <div className="absolute right-3 top-2.5 text-xs text-ink-faint" aria-live="polite">
                    Recherche…
                  </div>
                )}
                {suggestions.length > 0 && (
                  <>
                    <p className="sr-only" aria-live="polite">
                      {suggestions.length} résultat{suggestions.length > 1 ? 's' : ''} trouvé
                      {suggestions.length > 1 ? 's' : ''}.
                    </p>
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
                  </>
                )}
              </div>
              <Button variant="secondary" onClick={useMyPosition} disabled={locating} className="w-fit">
                {locating ? 'Localisation…' : '📍 Utiliser ma position'}
              </Button>
              {geoError && (
                <div id="location-search-error" role="alert" className="flex items-center gap-2 text-xs text-red-600">
                  <span>{geoError}</span>
                  <button
                    type="button"
                    onClick={() => setRetryToken((t) => t + 1)}
                    className="font-medium underline underline-offset-2"
                  >
                    Réessayer
                  </button>
                </div>
              )}

              <details className="rounded-lg border border-border p-3 text-sm">
                <summary className="cursor-pointer font-medium text-ink-soft">Saisir des coordonnées manuelles</summary>
                <div className="mt-3 flex flex-col gap-2">
                  <div className="grid grid-cols-2 gap-2">
                    <label className="flex flex-col gap-1 text-xs text-ink-faint">
                      Latitude
                      <input
                        value={manualLat}
                        onChange={(e) => setManualLat(e.target.value)}
                        placeholder="46.2263"
                        className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-500"
                      />
                    </label>
                    <label className="flex flex-col gap-1 text-xs text-ink-faint">
                      Longitude
                      <input
                        value={manualLon}
                        onChange={(e) => setManualLon(e.target.value)}
                        placeholder="7.1231"
                        className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-500"
                      />
                    </label>
                  </div>
                  {manualError && (
                    <p role="alert" className="text-xs text-red-600">
                      {manualError}
                    </p>
                  )}
                  <Button variant="secondary" type="button" onClick={applyManualCoordinates} className="w-fit">
                    Appliquer ces coordonnées
                  </Button>
                  <p className="text-xs text-ink-faint">
                    Une saisie manuelle est marquée comme telle (provenance « manuel ») et devra être confirmée
                    explicitement ci-dessous : l'altitude et le fuseau associés ne sont pas garantis tant qu'ils
                    n'ont pas été revalidés.
                  </p>
                </div>
              </details>

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

              <details className="rounded-lg border border-border p-3 text-sm">
                <summary className="cursor-pointer font-medium text-ink-soft">Corriger l'altitude manuellement</summary>
                <div className="mt-3 flex flex-col gap-2">
                  <label className="flex flex-col gap-1 text-xs text-ink-faint">
                    Nouvelle altitude (m)
                    <input
                      value={altitudeDraft}
                      onChange={(e) => setAltitudeDraft(e.target.value)}
                      placeholder="1200"
                      className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-500"
                    />
                  </label>
                  {altitudeError && (
                    <p role="alert" className="text-xs text-red-600">
                      {altitudeError}
                    </p>
                  )}
                  <Button variant="secondary" type="button" onClick={applyManualAltitude} className="w-fit">
                    Valider l'altitude
                  </Button>
                  <p className="text-xs text-ink-faint">Plage acceptée : -500 m à 9000 m.</p>
                </div>
              </details>
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

        <div className="flex flex-col gap-4">
          <Card title="Résumé de localisation">
            {/* No map is rendered here: this build ships no map library/tile
                provider, so we never promise a preview we cannot deliver
                (README_GC-COOLING-07 §7 "sinon retirer toute promesse de
                carte"). The page must stay fully usable without one. */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <MiniStat label="Adresse" value={study.location.address || '—'} />
              <MiniStat label="Fuseau horaire" value={study.location.timezone ?? '—'} />
              <MiniStat label="Commune" value={study.location.city ?? '—'} />
              <MiniStat
                label="Altitude"
                value={study.location.altitudeM != null ? `${study.location.altitudeM} m` : '—'}
              />
              <MiniStat label="Provenance" value={provenanceLabel(locationProvenance)} />
              <MiniStat
                label="Précision"
                value={study.location.longitude != null && locationProvenance === 'manual' ? 'Non vérifiée' : '—'}
              />
            </div>
            {hasDegradedData && study.location.latitude != null && (
              <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800">
                <p className="font-medium">Données estimées ou incomplètes</p>
                <p className="mt-1">
                  {locationProvenance === 'manual'
                    ? "Ces coordonnées ont été saisies manuellement et n'ont pas été vérifiées par un fournisseur."
                    : "Le fuseau horaire, l'altitude ou le contexte climatique ne sont pas encore complètement confirmés."}
                </p>
                <label className="mt-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={acknowledgedDegraded}
                    onChange={(e) => setAcknowledgedDegraded(e.target.checked)}
                  />
                  Je confirme utiliser ces données estimées en connaissance de cause.
                </label>
              </div>
            )}
          </Card>

          <ClimateContextCard scenarios={study.location.climateScenarios} />

          <Card>
            <div className="flex flex-col gap-3">
              <p className="text-sm text-ink-soft">
                Les scénarios climatiques ci-dessus sont recalculés à chaque lancement du calcul et reflètent la
                dernière analyse disponible pour ces coordonnées.
              </p>
              {confirmError && (
                <p role="alert" className="text-xs text-red-600">
                  {confirmError}
                </p>
              )}
              <div className="flex gap-3">
                <Button onClick={() => void confirm()} disabled={!canConfirm || confirming}>
                  {confirming ? 'Confirmation…' : 'Confirmer'}
                </Button>
                <Button variant="secondary" onClick={() => setAddress('')}>
                  Modifier la localisation
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <WizardFooter
        nextSteps={defaultNextSteps}
        onContinue={() => void confirm()}
        continueDisabled={!canConfirm || confirming}
      />
    </div>
  );
}

function provenanceLabel(provenance: LocationProvenance): string {
  switch (provenance) {
    case 'geocoded':
      return "Recherche d'adresse";
    case 'browser':
      return 'Position du navigateur';
    case 'manual':
      return 'Saisie manuelle';
    case 'imported':
      return 'Importée';
    default:
      return '—';
  }
}

function ClimateContextCard({ scenarios }: { scenarios: ClimateScenarioData[] }) {
  if (scenarios.length === 0) {
    return (
      <Card title="Contexte climatique">
        <p className="text-sm text-ink-soft">
          Contexte climatique non récupéré. Les scénarios (été de référence, forte chaleur, canicule prolongée)
          seront calculés à partir de ces coordonnées lors du premier lancement du calcul.
        </p>
      </Card>
    );
  }
  return (
    <Card title="Contexte climatique disponible">
      <div className="flex flex-col gap-3">
        {scenarios.map((s) => {
          const degraded = isDegradedScenario(s);
          const period = formatPeriod(s);
          return (
            <div key={s.id} className="rounded-lg border border-border p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink">{SCENARIO_LABELS[s.scenarioType] ?? s.scenarioType}</span>
                <span
                  className={
                    'rounded-full px-2 py-0.5 text-xs ' +
                    (degraded ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800')
                  }
                >
                  {degraded ? 'Estimation' : 'Historique observé'}
                </span>
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-ink-soft sm:grid-cols-4">
                <span>Extérieur : {s.outdoorTemperatureC.toFixed(1)} °C</span>
                <span>Humidité : {s.relativeHumidityPercent.toFixed(0)} %</span>
                <span>Rayonnement : {s.solarRadiationWm2.toFixed(0)} W/m²</span>
                <span>Vent : {s.windSpeedMs.toFixed(1)} m/s</span>
              </div>
              <div className="mt-2 text-xs text-ink-faint">
                {period && <span>Période : {period}. </span>}
                {s.providerCode && <span>Fournisseur : {s.providerCode}. </span>}
                <span>Provenance : {s.provenance}.</span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
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
