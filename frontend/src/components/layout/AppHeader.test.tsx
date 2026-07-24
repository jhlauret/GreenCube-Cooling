import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppHeader } from './AppHeader';
import { useUiStore } from '../../store/studyStore';

beforeEach(() => {
  useUiStore.setState({ helpOpen: false });
});

describe('AppHeader', () => {
  it('defaults to the "local" sync state when no prop is passed', () => {
    render(<AppHeader />);
    expect(screen.getByText('Brouillon local')).toBeInTheDocument();
  });

  it.each([
    ['local', 'Brouillon local'],
    ['dirty', 'Modifié — synchronisation en attente'],
    ['saving', 'Enregistrement…'],
    ['synced', 'Synchronisé avec Odoo'],
    ['error', 'Échec de synchronisation'],
    ['conflict', 'Conflit de version — modifié ailleurs'],
  ] as const)('renders the %s state with label "%s"', (syncState, label) => {
    render(<AppHeader syncState={syncState} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('never claims "Synchronisé avec Odoo" for a non-synced state (audit P0-04)', () => {
    render(<AppHeader syncState="dirty" />);
    expect(screen.queryByText('Synchronisé avec Odoo')).not.toBeInTheDocument();
  });

  it('surfaces the error message as a title attribute only in the error state', () => {
    render(<AppHeader syncState="error" syncErrorMessage="Réseau indisponible" />);
    expect(screen.getByText('Échec de synchronisation').closest('span')).toHaveAttribute(
      'title',
      'Réseau indisponible',
    );
  });

  it('does not show an error title when syncState is not "error", even with a message set', () => {
    render(<AppHeader syncState="synced" syncErrorMessage="stale message from a previous attempt" />);
    expect(screen.getByText('Synchronisé avec Odoo').closest('span')).not.toHaveAttribute('title');
  });

  it('toggles the help panel open and closed', async () => {
    const user = userEvent.setup();
    render(<AppHeader />);

    expect(screen.queryByText(/configurateur GreenCube Cooling/)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Aide/ }));
    expect(screen.getByText(/configurateur GreenCube Cooling/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Fermer' }));
    expect(screen.queryByText(/configurateur GreenCube Cooling/)).not.toBeInTheDocument();
  });

  it('closes the help panel on Escape (keyboard accessibility)', async () => {
    const user = userEvent.setup();
    render(<AppHeader />);

    await user.click(screen.getByRole('button', { name: /Aide/ }));
    expect(screen.getByRole('dialog', { name: 'Aide' })).toBeInTheDocument();

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('shows a "Recharger depuis Odoo" button only in the conflict state, and only when onReload is provided', () => {
    const { rerender } = render(<AppHeader syncState="conflict" />);
    expect(screen.queryByRole('button', { name: 'Recharger depuis Odoo' })).not.toBeInTheDocument();

    rerender(<AppHeader syncState="conflict" onReload={() => {}} />);
    expect(screen.getByRole('button', { name: 'Recharger depuis Odoo' })).toBeInTheDocument();

    rerender(<AppHeader syncState="synced" onReload={() => {}} />);
    expect(screen.queryByRole('button', { name: 'Recharger depuis Odoo' })).not.toBeInTheDocument();
  });

  it('calls onReload when the reload button is clicked', async () => {
    const user = userEvent.setup();
    const onReload = vi.fn();
    render(<AppHeader syncState="conflict" onReload={onReload} />);

    await user.click(screen.getByRole('button', { name: 'Recharger depuis Odoo' }));
    expect(onReload).toHaveBeenCalledTimes(1);
  });

  it('does not present the language indicator as an interactive dropdown', () => {
    render(<AppHeader />);
    const languageIndicator = screen.getByText('FR');
    expect(languageIndicator.tagName).not.toBe('BUTTON');
    expect(languageIndicator).toHaveAttribute('title', 'Interface disponible en français uniquement');
  });
});
