import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ResultsPage } from './ResultsPage';
import { useStudyStore } from '../store/studyStore';
import { createEmptyStudyDraft } from '../types/study';
import type { BackendResult, CalculationJob } from '../api/study';

vi.mock('../api/study', () => ({
  calculate: vi.fn(),
  getCalculationJob: vi.fn(),
  getResult: vi.fn(),
  getStudyResults: vi.fn(),
  ENERGYPLUS_TERMINAL_STATUSES: [
    'not_requested',
    'disabled',
    'translation_failed',
    'simulation_unavailable',
    'simulation_failed',
    'simulation_completed',
  ],
}));

function baseResult(overrides: Partial<BackendResult> = {}): BackendResult {
  return {
    id: 1,
    study_id: 1,
    job_id: 1,
    engine: 'MERCURE',
    engine_version: '1.0',
    requested_engine: 'quick_solver',
    energyplus_processing_status: 'not_requested',
    is_current: true,
    state: 'success',
    governing_scenario_code: 'hot_weather',
    sensible_load_w: 2720,
    latent_load_w: 360,
    total_load_w: 3080,
    shr: 0.88,
    margin_w: 420,
    recommended_capacity_w: 3500,
    recommended_capacity_kw: 3.5,
    recommended_capacity_btu_h: 11942,
    commercial_capacity: null,
    confidence_score: 0.9,
    warnings: [],
    main_load_drivers: [],
    breakdown: [],
    solar_gain_by_facade: [],
    duration_ms: 120,
    created_at: '2026-07-21T10:00:00Z',
    ...overrides,
  };
}

function renderResultsPage(navState?: { resultId?: number; jobId?: number }) {
  const study = createEmptyStudyDraft('draft-1', 'Test');
  const studyId = useStudyStore.getState().createStudy(study.name);
  useStudyStore.getState().updateStudy(studyId, { ...study, backendId: 42 });
  return render(
    <MemoryRouter
      initialEntries={[{ pathname: `/cooling/studies/${studyId}/results`, state: navState ?? null }]}
    >
      <Routes>
        <Route path="/cooling/studies/:studyId/results" element={<ResultsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  useStudyStore.setState({ studies: {} });
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe('ResultsPage', () => {
  it('consulting an existing result on direct visit never POSTs a new calculation', async () => {
    const { getStudyResults, calculate } = await import('../api/study');
    vi.mocked(getStudyResults).mockResolvedValue([baseResult()]);

    renderResultsPage();

    await waitFor(() => expect(getStudyResults).toHaveBeenCalledWith(42));
    await screen.findByText(/Puissance de refroidissement recommandée/);
    expect(calculate).not.toHaveBeenCalled();
  });

  it('fetches by navigation resultId without listing all study results', async () => {
    const { getResult, getStudyResults } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValue(baseResult({ id: 7 }));

    renderResultsPage({ resultId: 7 });

    await waitFor(() => expect(getResult).toHaveBeenCalledWith(7));
    expect(getStudyResults).not.toHaveBeenCalled();
  });

  it('shows a stale banner when the backend reports is_current: false', async () => {
    const { getResult } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValue(baseResult({ id: 7, is_current: false }));

    renderResultsPage({ resultId: 7 });

    await screen.findByText(/ne correspond plus à la version actuelle de l'étude/);
  });

  it('does not show a stale banner for the current result', async () => {
    const { getResult } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValue(baseResult({ id: 7, is_current: true }));

    renderResultsPage({ resultId: 7 });

    await screen.findByText(/Puissance de refroidissement recommandée/);
    expect(screen.queryByText(/ne correspond plus à la version actuelle/)).not.toBeInTheDocument();
  });

  it('shows the per-facade solar gain breakdown when the backend returns one (GC-COOLING-09 pt.11)', async () => {
    const { getResult } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValue(
      baseResult({
        id: 7,
        solar_gain_by_facade: [
          { facade: 'west', area_m2: 5, radiation_wm2: 420, solar_factor: 0.5, protection_factor: 1, gain_w: 1050 },
          { facade: 'north', area_m2: 1.5, radiation_wm2: 80, solar_factor: 0.5, protection_factor: 1, gain_w: 60 },
        ],
      }),
    );

    renderResultsPage({ resultId: 7 });

    await screen.findByText('Apports solaires par façade');
    expect(screen.getByText('Ouest')).toBeInTheDocument();
    expect(screen.getByText('Nord')).toBeInTheDocument();
    expect(screen.getByText('1050 W')).toBeInTheDocument();
  });

  it('does not show the per-facade solar gain card when the backend returns an empty list', async () => {
    const { getResult } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValue(baseResult({ id: 7, solar_gain_by_facade: [] }));

    renderResultsPage({ resultId: 7 });

    await screen.findByText(/Puissance de refroidissement recommandée/);
    expect(screen.queryByText('Apports solaires par façade')).not.toBeInTheDocument();
  });

  it(
    'polls the job for the EnergyPlus tail (real backoff) and stops once it reaches a terminal status',
    async () => {
      const { getResult, getCalculationJob } = await import('../api/study');
      vi.mocked(getResult).mockResolvedValue(
        baseResult({ id: 7, requested_engine: 'both', energyplus_processing_status: 'queued_for_worker' }),
      );

      const running: CalculationJob = {
        job_id: 5,
        status: 'completed',
        result_id: 7,
        energyplus_processing_status: 'simulation_running',
      };
      const completed: CalculationJob = {
        job_id: 5,
        status: 'completed',
        result_id: 7,
        energyplus_processing_status: 'simulation_completed',
      };
      vi.mocked(getCalculationJob).mockResolvedValueOnce(running).mockResolvedValueOnce(completed);

      renderResultsPage({ resultId: 7, jobId: 5 });

      await waitFor(() => expect(getCalculationJob).toHaveBeenCalledTimes(1));
      await screen.findByText(/Simulation EnergyPlus en cours/);

      // Real first backoff step is 3s; give it real wall-clock time to fire.
      await waitFor(() => expect(getCalculationJob).toHaveBeenCalledTimes(2), { timeout: 8000 });
      await screen.findByText(/Simulation EnergyPlus terminée/);

      // No further polling once terminal.
      await new Promise((resolve) => setTimeout(resolve, 500));
      expect(getCalculationJob).toHaveBeenCalledTimes(2);
    },
    12000,
  );

  it('never polls when the route is visited without a fresh jobId (e.g. refresh/history)', async () => {
    const { getResult, getCalculationJob } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValue(baseResult({ id: 7 }));

    renderResultsPage({ resultId: 7 });

    await screen.findByText(/Puissance de refroidissement recommandée/);
    await new Promise((resolve) => setTimeout(resolve, 500));
    expect(getCalculationJob).not.toHaveBeenCalled();
  });

  it('rerun creates exactly one new job per click and ignores a rapid second click while in flight', async () => {
    const { getResult, calculate } = await import('../api/study');
    vi.mocked(getResult).mockResolvedValueOnce(baseResult({ id: 7 }));
    let resolveCalculate: (job: CalculationJob) => void = () => {};
    vi.mocked(calculate).mockReturnValue(
      new Promise((resolve) => {
        resolveCalculate = resolve;
      }),
    );

    renderResultsPage({ resultId: 7 });
    await screen.findByText(/Puissance de refroidissement recommandée/);

    const user = userEvent.setup();
    const button = screen.getByRole('button', { name: /Relancer le calcul/ });
    await user.click(button);
    await user.click(button); // rapid double-click while the first POST is in flight

    expect(calculate).toHaveBeenCalledTimes(1);

    vi.mocked(getResult).mockResolvedValueOnce(baseResult({ id: 9 }));
    resolveCalculate({ job_id: 8, status: 'completed', result_id: 9, energyplus_processing_status: 'not_requested' });

    await waitFor(() => expect(getResult).toHaveBeenCalledWith(9));
  });
});
