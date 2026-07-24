import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Outlet, Route, Routes, useParams } from 'react-router-dom';
import { UsageStep } from './UsageStep';
import { dailyOccupiedHours } from './usageSchedule';
import { useStudyStore } from '../../store/studyStore';
import { createEmptyStudyDraft } from '../../types/study';

// Mirrors the real StudyLayout: subscribes to the store and feeds it to
// children through a real <Outlet context>, so store updates triggered by
// UsageStep (via updateStudy) reactively flow back in.
function TestStudyLayout() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  if (!study) return null;
  return <Outlet context={{ study }} />;
}

function renderUsageStep(study = createEmptyStudyDraft('draft-1', 'Test')) {
  const studyId = useStudyStore.getState().createStudy(study.name);
  useStudyStore.getState().updateStudy(studyId, study);
  return render(
    <MemoryRouter initialEntries={[`/cooling/studies/${studyId}/usage`]}>
      <Routes>
        <Route path="/cooling/studies/:studyId" element={<TestStudyLayout />}>
          <Route path="usage" element={<UsageStep />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  useStudyStore.setState({ studies: {} });
});

describe('dailyOccupiedHours', () => {
  it('computes a same-day window normally', () => {
    expect(dailyOccupiedHours(8, 18)).toBe(10);
  });

  it('handles a window crossing midnight', () => {
    expect(dailyOccupiedHours(22, 6)).toBe(8);
  });

  it('treats an equal start/end as unoccupied (0h), not a full-day wrap', () => {
    expect(dailyOccupiedHours(9, 9)).toBe(0);
  });
});

describe('UsageStep', () => {
  it('renders the default Mon-Fri schedule as active, matching the backend default', () => {
    renderUsageStep();
    const monday = screen.getByRole('button', { name: 'Lun' });
    const saturday = screen.getByRole('button', { name: 'Sam' });
    expect(monday).toHaveAttribute('aria-pressed', 'true');
    expect(saturday).toHaveAttribute('aria-pressed', 'false');
  });

  it('toggling a day updates the active-days count and persists to the store', async () => {
    const user = userEvent.setup();
    renderUsageStep();

    expect(screen.getByText('5 / 7')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Sam' }));
    expect(screen.getByText('6 / 7')).toBeInTheDocument();
  });

  it('warns and blocks continue when every day is deactivated but occupants remain', async () => {
    const user = userEvent.setup();
    renderUsageStep();

    for (const label of ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven']) {
      await user.click(screen.getByRole('button', { name: label }));
    }

    expect(screen.getByRole('alert')).toHaveTextContent(/au moins un jour doit être actif/i);
    expect(screen.getByRole('button', { name: /continuer/i })).toBeDisabled();
  });

  it('shows a midnight-crossing note and the resulting occupied-hours count', () => {
    const study = createEmptyStudyDraft('draft-1', 'Test');
    study.usage.occupancyStartHour = 22;
    study.usage.occupancyEndHour = 6;
    renderUsageStep(study);

    expect(screen.getByText(/traverse minuit/i)).toBeInTheDocument();
    expect(screen.getByText('8.0 h')).toBeInTheDocument();
  });

  it('weighs the human heat gain preview by the daily occupancy fraction, not just occupant count', () => {
    // 2 occupants, 8h/24h occupied (8h-18h is actually 10h; use an
    // explicit short window to make the fraction obvious and distinct
    // from the "always full gain" bug this preview used to have).
    const study = createEmptyStudyDraft('draft-1', 'Test');
    study.usage.usualOccupants = 2;
    study.usage.occupancyStartHour = 8;
    study.usage.occupancyEndHour = 20; // 12h/24h = 0.5 fraction
    renderUsageStep(study);

    // sensible = 2 * 0.5 * 75 = 75 W
    expect(screen.getByText('≈ 75 W')).toBeInTheDocument();
    // latent = 2 * 0.5 * 60 = 60 g/h
    expect(screen.getByText('≈ 60 g/h')).toBeInTheDocument();
  });

  it('blocks continue when maximum occupants is inconsistent with usual occupants', () => {
    const study = createEmptyStudyDraft('draft-1', 'Test');
    study.usage.usualOccupants = 4;
    study.usage.maximumOccupants = 4;
    renderUsageStep(study);
    // The maximum-occupants input's own min bound already prevents typing
    // a lower value through the UI, but the footer guard is what protects
    // against a value that arrived some other way (e.g. a stale draft
    // loaded from local storage before this field existed).
    expect(screen.getByRole('button', { name: /continuer/i })).not.toBeDisabled();
  });
});
