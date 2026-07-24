import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { EquipmentSelectionPage } from './EquipmentSelectionPage';
import { useStudyStore } from '../store/studyStore';
import { createEmptyStudyDraft } from '../types/study';
import {
  getEquipmentRecommendations,
  listEquipmentSelections,
  postEquipmentSelection,
  validateEquipmentSelection,
  type EquipmentRecommendation,
  type EquipmentSelection,
} from '../api/study';

vi.mock('../api/study', () => ({
  getEquipmentRecommendations: vi.fn(),
  listEquipmentSelections: vi.fn(),
  postEquipmentSelection: vi.fn(),
  validateEquipmentSelection: vi.fn(),
}));

const mockedGetRecommendations = vi.mocked(getEquipmentRecommendations);
const mockedListSelections = vi.mocked(listEquipmentSelections);
const mockedPostSelection = vi.mocked(postEquipmentSelection);
const mockedValidateSelection = vi.mocked(validateEquipmentSelection);

const RECOMMENDED: EquipmentRecommendation = {
  product: {
    id: 501,
    name: 'Split mural 3.5kW',
    type: 'split_wall',
    nominal_capacity_w: 3500,
    capacity_at_35c_w: 3300,
    capacity_at_45c_w: 3100,
    electrical_power_w: 900,
    eer: 3.4,
    seer: 6.1,
    shr: 0.82,
    noise_db: 21,
    max_outdoor_temperature_c: 46,
    power_supply: 'monophase',
    data_quality: 'catalog',
    list_price: 1200,
  },
  status: 'recommended',
  reasons: ['Capacité bien ajustée au besoin recommandé, y compris à haute température.'],
  oversizing_ratio: 1.1,
};

const INSUFFICIENT: EquipmentRecommendation = {
  product: {
    id: 502,
    name: 'Modèle sans fiche technique complète',
    type: 'split_wall',
    nominal_capacity_w: 0,
    capacity_at_35c_w: 0,
    capacity_at_45c_w: 0,
    electrical_power_w: 0,
    eer: 0,
    seer: 0,
    shr: 0,
    noise_db: 0,
    max_outdoor_temperature_c: 0,
    power_supply: 'monophase',
    data_quality: 'missing',
    list_price: 0,
  },
  status: 'insufficient_data',
  reasons: ['Données techniques insuffisantes pour évaluer la compatibilité : capacity_at_45c_w.'],
  oversizing_ratio: null,
};

function renderPage(study = createEmptyStudyDraft('draft-1', 'Étude test')) {
  const studyId = useStudyStore.getState().createStudy(study.name);
  useStudyStore.getState().updateStudy(studyId, { ...study, backendId: 42 });
  return render(
    <MemoryRouter initialEntries={[`/cooling/studies/${studyId}/equipment-selection`]}>
      <Routes>
        <Route path="/cooling/studies/:studyId/equipment-selection" element={<EquipmentSelectionPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  useStudyStore.setState({ studies: {} });
  vi.clearAllMocks();
  mockedGetRecommendations.mockResolvedValue([RECOMMENDED, INSUFFICIENT]);
  mockedListSelections.mockResolvedValue([]);
});

describe('EquipmentSelectionPage', () => {
  it('renders backend-ordered recommendations without re-sorting client-side', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Split mural 3.5kW')).toBeInTheDocument());
    const cards = screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent);
    // Backend order is preserved as-is (recommended first, insufficient_data second).
    expect(cards).toEqual(['Split mural 3.5kW', 'Modèle sans fiche technique complète']);
  });

  it('disables selection for a product with insufficient technical data', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Modèle sans fiche technique complète')).toBeInTheDocument());
    const button = screen.getByRole('button', { name: 'Données insuffisantes' });
    expect(button).toBeDisabled();
  });

  it('selects a recommended product', async () => {
    mockedPostSelection.mockResolvedValue(undefined);
    renderPage();
    await waitFor(() => expect(screen.getByText('Split mural 3.5kW')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: 'Sélectionner' }));
    await waitFor(() => expect(mockedPostSelection).toHaveBeenCalledWith(42, 501));
  });

  it('shows a "Valider" action for a selected (not yet validated) history row and calls the validate endpoint', async () => {
    const selection: EquipmentSelection = {
      id: 9,
      product_id: 501,
      product_name: 'Split mural 3.5kW',
      capacity_at_45c_w: 3100,
      max_outdoor_temperature_c: 46,
      shr: 0.82,
      eer: 3.4,
      nominal_capacity_w: 3500,
      price: 1200,
      currency: 'EUR',
      compatibility_status: 'recommended',
      state: 'selected',
      result_id: 7,
      created_at: '2026-07-20T10:00:00Z',
      validated_at: null,
      validator_id: null,
      supersedes_id: null,
    };
    mockedListSelections.mockResolvedValue([selection]);
    mockedValidateSelection.mockResolvedValue({ ...selection, state: 'validated', validated_at: '2026-07-23T10:00:00Z' });
    renderPage();

    await screen.findByText('Historique des sélections');
    await userEvent.click(screen.getByRole('button', { name: 'Valider' }));
    await waitFor(() => expect(mockedValidateSelection).toHaveBeenCalledWith(42, 9));
  });
});
