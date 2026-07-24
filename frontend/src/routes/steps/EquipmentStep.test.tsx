import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Outlet, Route, Routes, useParams } from 'react-router-dom';
import { EquipmentStep } from './EquipmentStep';
import { useStudyStore } from '../../store/studyStore';
import { createEmptyStudyDraft } from '../../types/study';
import type { EquipmentLoadCatalogItem } from '../../api/study';

vi.mock('../../api/study', () => ({
  getEquipmentLoadCatalog: vi.fn(),
}));

// Mirrors the real StudyLayout: subscribes to the store and feeds it to
// children through a real <Outlet context>, matching production.
function TestStudyLayout() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  if (!study) return null;
  return <Outlet context={{ study }} />;
}

const CATALOG: EquipmentLoadCatalogItem[] = [
  {
    id: 101,
    code: 'laptop',
    name: 'Ordinateur portable',
    category: 'it',
    unit_power_w: 45,
    usage_hours_per_day: 8,
    simultaneity_percent: 100,
    data_quality: 'catalog',
  },
  {
    id: 102,
    code: 'ups',
    name: 'Onduleur',
    category: 'inverter',
    unit_power_w: 600,
    usage_hours_per_day: 24,
    simultaneity_percent: 100,
    data_quality: 'catalog',
  },
];

function renderEquipmentStep(study = createEmptyStudyDraft('draft-1', 'Test')) {
  const studyId = useStudyStore.getState().createStudy(study.name);
  useStudyStore.getState().updateStudy(studyId, study);
  return render(
    <MemoryRouter initialEntries={[`/cooling/studies/${studyId}/equipment`]}>
      <Routes>
        <Route path="/cooling/studies/:studyId" element={<TestStudyLayout />}>
          <Route path="equipment" element={<EquipmentStep />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(async () => {
  useStudyStore.setState({ studies: {} });
  const { getEquipmentLoadCatalog } = await import('../../api/study');
  vi.mocked(getEquipmentLoadCatalog).mockResolvedValue(CATALOG);
});

describe('EquipmentStep', () => {
  it('fetches the internal-loads catalog from Odoo instead of using a hardcoded list', async () => {
    const { getEquipmentLoadCatalog } = await import('../../api/study');
    renderEquipmentStep();
    await waitFor(() => expect(getEquipmentLoadCatalog).toHaveBeenCalled());
    expect(await screen.findByText('Ordinateur portable')).toBeInTheDocument();
  });

  it('shows a loading state before the catalog resolves', async () => {
    const { getEquipmentLoadCatalog } = await import('../../api/study');
    let resolveCatalog: (value: EquipmentLoadCatalogItem[]) => void = () => {};
    vi.mocked(getEquipmentLoadCatalog).mockReturnValue(
      new Promise((resolve) => {
        resolveCatalog = resolve;
      }),
    );

    renderEquipmentStep();
    expect(screen.getByText(/Chargement du catalogue/)).toBeInTheDocument();

    resolveCatalog(CATALOG);
    await waitFor(() => expect(screen.queryByText(/Chargement du catalogue/)).not.toBeInTheDocument());
  });

  it('shows an error message when the catalog fails to load', async () => {
    const { getEquipmentLoadCatalog } = await import('../../api/study');
    vi.mocked(getEquipmentLoadCatalog).mockRejectedValue(new Error('network down'));

    renderEquipmentStep();
    await waitFor(() => expect(screen.getByText('network down')).toBeInTheDocument());
  });

  it('selecting a catalog item adds it with the catalog product_id and category, not a hardcoded value', async () => {
    const user = userEvent.setup();
    renderEquipmentStep();

    const checkbox = await screen.findByLabelText('Sélectionner Onduleur');
    await user.click(checkbox);

    const id = Object.keys(useStudyStore.getState().studies)[0];
    const line = useStudyStore.getState().studies[id].equipment.find((e) => e.id === 'ups');
    expect(line).toBeDefined();
    expect(line?.productId).toBe(102);
    expect(line?.category).toBe('inverter');
    expect(line?.unitPowerW).toBe(600);
  });

  it('unchecking a selected item removes it from the study', async () => {
    const user = userEvent.setup();
    renderEquipmentStep();

    const checkbox = await screen.findByLabelText('Sélectionner Ordinateur portable');
    await user.click(checkbox);
    await waitFor(() => {
      const id = Object.keys(useStudyStore.getState().studies)[0];
      expect(useStudyStore.getState().studies[id].equipment).toHaveLength(1);
    });

    await user.click(checkbox);
    const id = Object.keys(useStudyStore.getState().studies)[0];
    expect(useStudyStore.getState().studies[id].equipment).toHaveLength(0);
  });
});
