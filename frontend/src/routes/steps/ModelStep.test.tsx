import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Outlet, Route, Routes, useParams } from 'react-router-dom';
import { ModelStep } from './ModelStep';
import { useStudyStore } from '../../store/studyStore';
import { createEmptyStudyDraft } from '../../types/study';
import type { BackendThermalSpecification } from '../../api/study';

vi.mock('../../api/study', () => ({
  getThermalSpecificationTemplates: vi.fn(),
}));

// Mirrors the real StudyLayout: subscribes to the store and feeds it to
// children through a real <Outlet context>, so store updates triggered by
// ModelStep (via updateStudy) reactively flow back in — exactly like
// production, and unlike a static mocked useOutletContext would.
function TestStudyLayout() {
  const { studyId } = useParams<{ studyId: string }>();
  const study = useStudyStore((state) => (studyId ? state.studies[studyId] : undefined));
  if (!study) return null;
  return <Outlet context={{ study }} />;
}

const TEMPLATES: BackendThermalSpecification[] = [
  {
    id: 10,
    code: 'gc-studio',
    version: '1.0',
    standard_model: true,
    source_template_id: null,
    source_template_version: null,
    length_m: 4,
    width_m: 2.5,
    height_m: 2.5,
    wall_u_value: 0.18,
    roof_u_value: 0.16,
    floor_u_value: 0.2,
    airtightness_n50: 0.6,
    thermal_mass_level: 'medium',
    notes: false,
    facades: [],
  },
  {
    id: 11,
    code: 'gc-office',
    version: '1.0',
    standard_model: true,
    source_template_id: null,
    source_template_version: null,
    length_m: 6,
    width_m: 3,
    height_m: 2.7,
    wall_u_value: 0.2,
    roof_u_value: 0.18,
    floor_u_value: 0.22,
    airtightness_n50: 0.8,
    thermal_mass_level: 'medium',
    notes: false,
    facades: [],
  },
];

function renderModelStep(study = createEmptyStudyDraft('draft-1', 'Test')) {
  const studyId = useStudyStore.getState().createStudy(study.name);
  useStudyStore.getState().updateStudy(studyId, study);
  return render(
    <MemoryRouter initialEntries={[`/cooling/studies/${studyId}/model`]}>
      <Routes>
        <Route path="/cooling/studies/:studyId" element={<TestStudyLayout />}>
          <Route path="model" element={<ModelStep />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(async () => {
  useStudyStore.setState({ studies: {} });
  const { getThermalSpecificationTemplates } = await import('../../api/study');
  vi.mocked(getThermalSpecificationTemplates).mockResolvedValue(TEMPLATES);
});

describe('ModelStep', () => {
  it('fetches the catalog instead of using hardcoded model data', async () => {
    const { getThermalSpecificationTemplates } = await import('../../api/study');
    renderModelStep();
    await waitFor(() => expect(getThermalSpecificationTemplates).toHaveBeenCalled());
  });

  it('auto-applies the studio template on first load, matching the default card', async () => {
    renderModelStep();
    await waitFor(() => {
      expect(screen.getByText(/4 x 2\.5 x 2\.5 m/)).toBeInTheDocument();
    });
  });

  it('selecting a different model card applies its real dimensions, not a hardcoded default', async () => {
    const user = userEvent.setup();
    renderModelStep();

    await screen.findByText(/GreenCube Bureau/);
    await user.click(screen.getByText(/GreenCube Bureau/));

    await waitFor(() => {
      // "Spécifications du modèle" summary reflects the office template's own dimensions.
      expect(screen.getByText('6.00 x 3.00 x 2.70 m')).toBeInTheDocument();
    });
  });

  it('shows a loading state before the catalog resolves', async () => {
    const { getThermalSpecificationTemplates } = await import('../../api/study');
    let resolveTemplates: (value: BackendThermalSpecification[]) => void = () => {};
    vi.mocked(getThermalSpecificationTemplates).mockReturnValue(
      new Promise((resolve) => {
        resolveTemplates = resolve;
      }),
    );

    renderModelStep();
    expect(screen.getByText(/Chargement du catalogue GreenCube/)).toBeInTheDocument();

    resolveTemplates(TEMPLATES);
    await waitFor(() => expect(screen.queryByText(/Chargement du catalogue GreenCube/)).not.toBeInTheDocument());
  });

  it('shows an error message when the catalog fails to load', async () => {
    const { getThermalSpecificationTemplates } = await import('../../api/study');
    vi.mocked(getThermalSpecificationTemplates).mockRejectedValue(new Error('network down'));

    renderModelStep();
    // ModelStep surfaces err.message directly for a real Error instance;
    // the generic "Impossible de charger..." fallback only applies to
    // non-Error rejections.
    await waitFor(() => expect(screen.getByText('network down')).toBeInTheDocument());
  });

  it('falls back to a generic message for a non-Error rejection', async () => {
    const { getThermalSpecificationTemplates } = await import('../../api/study');
    vi.mocked(getThermalSpecificationTemplates).mockRejectedValue('not an Error instance');

    renderModelStep();
    await waitFor(() =>
      expect(screen.getByText(/Impossible de charger le catalogue GreenCube/)).toBeInTheDocument(),
    );
  });

  it('applies distinct roof/floor U-values per catalog model, not a fixed ratio of the wall value', async () => {
    const user = userEvent.setup();
    renderModelStep();
    const store = useStudyStore;
    const id = Object.keys(store.getState().studies)[0];

    await waitFor(() => expect(store.getState().studies[id].model.roofUValueWm2k).toBe(0.16));
    expect(store.getState().studies[id].model.floorUValueWm2k).toBe(0.2);

    await screen.findByText(/GreenCube Bureau/);
    await user.click(screen.getByText(/GreenCube Bureau/));

    await waitFor(() => {
      expect(store.getState().studies[id].model.roofUValueWm2k).toBe(0.18);
      expect(store.getState().studies[id].model.floorUValueWm2k).toBe(0.22);
    });
  });

  it('lets the user edit wall/roof/floor U-values individually in custom mode', async () => {
    const user = userEvent.setup();
    renderModelStep();

    await screen.findByText(/GreenCube Personnalisé/);
    await user.click(screen.getByText(/GreenCube Personnalisé/));

    const roofInput = await screen.findByLabelText('Toiture');
    await user.clear(roofInput);
    await user.type(roofInput, '0.33');

    const id = Object.keys(useStudyStore.getState().studies)[0];
    await waitFor(() => expect(useStudyStore.getState().studies[id].model.roofUValueWm2k).toBeCloseTo(0.33));
    // Wall/floor U-values are untouched by editing the roof field alone.
    expect(useStudyStore.getState().studies[id].model.floorUValueWm2k).toBe(0.2);
  });

  it('flags the model as "modifié pour cette étude" once a customization diverges from the applied template', async () => {
    const user = userEvent.setup();
    renderModelStep();

    await waitFor(() => expect(screen.getByText(/Valeurs héritées du catalogue Odoo/)).toBeInTheDocument());

    await user.click(screen.getByText(/GreenCube Personnalisé/));
    const roofInput = await screen.findByLabelText('Toiture');
    await user.clear(roofInput);
    await user.type(roofInput, '0.9');

    // Re-selecting the studio card re-applies the template's exact values,
    // clearing the customization — then diverge again to check the badge.
    await user.click(screen.getByText(/GreenCube Studio/));
    await user.click(screen.getByText(/GreenCube Personnalisé/));
    const roofInput2 = await screen.findByLabelText('Toiture');
    await user.clear(roofInput2);
    await user.type(roofInput2, '0.9');

    await waitFor(() => expect(screen.getByText('Modifié pour cette étude')).toBeInTheDocument());
    expect(screen.getByText('Réappliquer le modèle catalogue')).toBeInTheDocument();
  });

  it('reapplying the catalog template asks for confirmation and restores the inherited values', async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderModelStep();

    await waitFor(() => expect(screen.getByText(/Valeurs héritées du catalogue Odoo/)).toBeInTheDocument());
    await user.click(screen.getByText(/GreenCube Personnalisé/));
    const roofInput = await screen.findByLabelText('Toiture');
    await user.clear(roofInput);
    await user.type(roofInput, '0.9');

    await waitFor(() => expect(screen.getByText('Modifié pour cette étude')).toBeInTheDocument());
    await user.click(screen.getByText('Réappliquer le modèle catalogue'));

    expect(confirmSpy).toHaveBeenCalled();
    const id = Object.keys(useStudyStore.getState().studies)[0];
    await waitFor(() => expect(useStudyStore.getState().studies[id].model.roofUValueWm2k).toBe(0.16));
    confirmSpy.mockRestore();
  });

  it('does not apply the reapply-template change when the user cancels the confirmation', async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderModelStep();

    await waitFor(() => expect(screen.getByText(/Valeurs héritées du catalogue Odoo/)).toBeInTheDocument());
    await user.click(screen.getByText(/GreenCube Personnalisé/));
    const roofInput = await screen.findByLabelText('Toiture');
    await user.clear(roofInput);
    await user.type(roofInput, '0.9');

    await waitFor(() => expect(screen.getByText('Modifié pour cette étude')).toBeInTheDocument());
    await user.click(screen.getByText('Réappliquer le modèle catalogue'));

    expect(confirmSpy).toHaveBeenCalled();
    const id = Object.keys(useStudyStore.getState().studies)[0];
    expect(useStudyStore.getState().studies[id].model.roofUValueWm2k).toBeCloseTo(0.9);
    confirmSpy.mockRestore();
  });
});
