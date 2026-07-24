import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Outlet, Route, Routes, useParams } from 'react-router-dom';
import { LocationStep } from './LocationStep';
import { useStudyStore } from '../../store/studyStore';
import { createEmptyStudyDraft } from '../../types/study';
import type { StudyDraft } from '../../types/study';

vi.mock('../../api/geo', () => ({
  searchAddress: vi.fn(),
  fetchGeoContext: vi.fn(),
  confirmLocation: vi.fn(),
}));

// Mirrors the real StudyLayout: subscribes to the store and feeds it to
// children through a real <Outlet context>, exactly like production.
function TestStudyLayout() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  if (!study) return null;
  return <Outlet context={{ study }} />;
}

function renderLocationStep(patch: Partial<StudyDraft> = {}) {
  const draft = createEmptyStudyDraft('draft-1', 'Test');
  const studyId = useStudyStore.getState().createStudy(draft.name);
  useStudyStore.getState().updateStudy(studyId, { ...draft, ...patch });
  render(
    <MemoryRouter initialEntries={[`/cooling/studies/${studyId}/location`]}>
      <Routes>
        <Route path="/cooling/studies/:studyId" element={<TestStudyLayout />}>
          <Route path="location" element={<LocationStep />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
  return studyId;
}

beforeEach(async () => {
  useStudyStore.setState({ studies: {} });
  const geo = await import('../../api/geo');
  vi.mocked(geo.searchAddress).mockResolvedValue([]);
  vi.mocked(geo.fetchGeoContext).mockResolvedValue({ altitude_m: 1200, timezone: 'Europe/Zurich', utc_offset_seconds: 3600 });
  vi.mocked(geo.confirmLocation).mockResolvedValue({});
});

describe('LocationStep — search', () => {
  it('shows a retry action when the address search fails, and retrying re-issues the request', async () => {
    const user = userEvent.setup();
    const geo = await import('../../api/geo');
    vi.mocked(geo.searchAddress).mockRejectedValue(new Error('network down'));

    renderLocationStep();
    await user.type(screen.getByPlaceholderText('Adresse, commune ou coordonnées GPS'), 'Mission');

    await waitFor(() => expect(screen.getByText(/indisponible pour le moment/)).toBeInTheDocument());
    expect(geo.searchAddress).toHaveBeenCalledTimes(1);

    vi.mocked(geo.searchAddress).mockResolvedValue([]);
    await user.click(screen.getByText('Réessayer'));
    await waitFor(() => expect(geo.searchAddress).toHaveBeenCalledTimes(2));
  });
});

describe('LocationStep — manual coordinates', () => {
  it('rejects an out-of-range latitude', async () => {
    const user = userEvent.setup();
    renderLocationStep();

    await user.click(screen.getByText('Saisir des coordonnées manuelles'));
    await user.type(screen.getByPlaceholderText('46.2263'), '120');
    await user.type(screen.getByPlaceholderText('7.1231'), '7.1');
    await user.click(screen.getByText('Appliquer ces coordonnées'));

    expect(screen.getByText(/latitude doit être comprise entre -90 et 90/)).toBeInTheDocument();
  });

  it('rejects an out-of-range longitude', async () => {
    const user = userEvent.setup();
    renderLocationStep();

    await user.click(screen.getByText('Saisir des coordonnées manuelles'));
    await user.type(screen.getByPlaceholderText('46.2263'), '46');
    await user.type(screen.getByPlaceholderText('7.1231'), '200');
    await user.click(screen.getByText('Appliquer ces coordonnées'));

    expect(screen.getByText(/longitude doit être comprise entre -180 et 180/)).toBeInTheDocument();
  });

  it('accepts a comma decimal separator and applies coordinates, marking provenance manual', async () => {
    const user = userEvent.setup();
    const studyId = renderLocationStep();

    await user.click(screen.getByText('Saisir des coordonnées manuelles'));
    await user.type(screen.getByPlaceholderText('46.2263'), '46,2263');
    await user.type(screen.getByPlaceholderText('7.1231'), '7,1231');
    await user.click(screen.getByText('Appliquer ces coordonnées'));

    await waitFor(() => {
      const study = useStudyStore.getState().studies[studyId];
      expect(study.location.latitude).toBeCloseTo(46.2263);
      expect(study.location.longitude).toBeCloseTo(7.1231);
    });
  });

  it('requires an explicit acknowledgement before confirming manually-entered coordinates', async () => {
    const user = userEvent.setup();
    renderLocationStep();

    await user.click(screen.getByText('Saisir des coordonnées manuelles'));
    await user.type(screen.getByPlaceholderText('46.2263'), '46.2263');
    await user.type(screen.getByPlaceholderText('7.1231'), '7.1231');
    await user.click(screen.getByText('Appliquer ces coordonnées'));

    await waitFor(() => expect(screen.getByText(/Données estimées ou incomplètes/)).toBeInTheDocument());
    const confirmButton = screen.getByRole('button', { name: /^Confirmer$/ });
    expect(confirmButton).toBeDisabled();

    await user.click(screen.getByLabelText(/Je confirme utiliser ces données estimées/));
    expect(confirmButton).not.toBeDisabled();
  });
});

describe('LocationStep — altitude correction', () => {
  it('rejects an altitude outside -500..9000', async () => {
    const user = userEvent.setup();
    renderLocationStep();

    await user.click(screen.getByText("Corriger l'altitude manuellement"));
    await user.type(screen.getByPlaceholderText('1200'), '9500');
    await user.click(screen.getByText("Valider l'altitude"));

    expect(screen.getByText(/altitude doit être comprise entre -500 m et 9000 m/)).toBeInTheDocument();
  });

  it('applies a valid manual altitude override', async () => {
    const user = userEvent.setup();
    const studyId = renderLocationStep({
      location: { ...createEmptyStudyDraft('x', 'x').location, latitude: 46, longitude: 7, altitudeM: 500 },
    });

    await user.click(screen.getByText("Corriger l'altitude manuellement"));
    await user.type(screen.getByPlaceholderText('1200'), '1234');
    await user.click(screen.getByText("Valider l'altitude"));

    await waitFor(() => expect(useStudyStore.getState().studies[studyId].location.altitudeM).toBe(1234));
  });
});

describe('LocationStep — climate context', () => {
  it('shows the "not fetched yet" message when no scenarios are available', () => {
    renderLocationStep();
    expect(screen.getByText(/Contexte climatique non récupéré/)).toBeInTheDocument();
  });

  it('renders available scenarios with period, provenance and key values', () => {
    renderLocationStep({
      location: {
        ...createEmptyStudyDraft('x', 'x').location,
        latitude: 46,
        longitude: 7,
        climateScenarios: [
          {
            id: 1,
            scenarioType: 'reference_summer',
            outdoorTemperatureC: 31.8,
            relativeHumidityPercent: 45,
            solarRadiationWm2: 620,
            windSpeedMs: 2.1,
            provenance: 'api',
            datasetType: 'historical_observed',
            checksum: 'abc123',
            referenceDate: null,
            dataStart: '2013-01-01',
            dataEnd: '2023-12-31',
            sampleDays: 3650,
            providerCode: 'open-meteo',
            providerVersion: '1.0',
            timezone: 'Europe/Zurich',
            license: 'CC-BY',
          },
        ],
      },
    });

    expect(screen.getByText('Été de référence')).toBeInTheDocument();
    expect(screen.getByText(/31\.8 °C/)).toBeInTheDocument();
    expect(screen.getByText(/2013-01-01 → 2023-12-31/)).toBeInTheDocument();
    expect(screen.getByText('Historique observé')).toBeInTheDocument();
  });

  it('flags a fallback/estimated scenario as an estimation, not real historical data', () => {
    renderLocationStep({
      location: {
        ...createEmptyStudyDraft('x', 'x').location,
        latitude: 46,
        longitude: 7,
        climateScenarios: [
          {
            id: 2,
            scenarioType: 'hot_weather',
            outdoorTemperatureC: 34,
            relativeHumidityPercent: 40,
            solarRadiationWm2: 700,
            windSpeedMs: 1.5,
            provenance: 'estimated_reference',
            datasetType: null,
            checksum: null,
            referenceDate: null,
            dataStart: null,
            dataEnd: null,
            sampleDays: null,
            providerCode: null,
            providerVersion: null,
            timezone: null,
            license: null,
          },
        ],
      },
    });

    expect(screen.getByText('Estimation')).toBeInTheDocument();
  });
});

describe('LocationStep — confirmation', () => {
  it('keeps the Confirm button disabled until coordinates exist', () => {
    renderLocationStep();
    expect(screen.getByRole('button', { name: /^Confirmer$/ })).toBeDisabled();
  });

  it('is enabled immediately for a geocoded (non-degraded) location with timezone and altitude present', async () => {
    renderLocationStep({
      location: {
        ...createEmptyStudyDraft('x', 'x').location,
        latitude: 46,
        longitude: 7,
        altitudeM: 1200,
        timezone: 'Europe/Zurich',
        locationProvenance: 'geocoded',
        climateScenarios: [],
      },
    });
    expect(screen.getByRole('button', { name: /^Confirmer$/ })).not.toBeDisabled();
  });
});
