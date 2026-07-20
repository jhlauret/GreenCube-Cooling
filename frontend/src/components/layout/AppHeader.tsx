import { useEffect } from 'react';
import { useUiStore } from '../../store/studyStore';

/**
 * - local: never synced to Odoo yet (or no active study).
 * - dirty: edited locally since the last successful sync.
 * - saving: an autosave request is currently in flight.
 * - synced: local draft matches what was last pushed to Odoo.
 * - error: the last autosave attempt failed (see syncErrorMessage).
 */
export type SyncState = 'local' | 'dirty' | 'saving' | 'synced' | 'error';

const SYNC_STATE_DISPLAY: Record<SyncState, { icon: string; label: string }> = {
  local: { icon: '📝', label: 'Brouillon local' },
  dirty: { icon: '✏️', label: 'Modifié — synchronisation en attente' },
  saving: { icon: '🔄', label: 'Enregistrement…' },
  synced: { icon: '☁️', label: 'Synchronisé avec Odoo' },
  error: { icon: '⚠️', label: 'Échec de synchronisation' },
};

/**
 * `syncState` must be passed explicitly by any page that knows whether the
 * current study has actually been pushed to Odoo — defaulting to a false
 * "Enregistré" claim before any sync happened was audit finding P0-04.
 * The wizard step pages (StudyLayout) derive it from a real debounced
 * autosave (see sync/useAutosave.ts); Review/Results/EquipmentSelection
 * still only distinguish local/synced since they sync synchronously
 * before their own explicit actions.
 *
 * The "Aide"/"FR" controls used to be pure decoration (no handler, no
 * language switching infrastructure anywhere in the app) — audit
 * GC-COOLING-06 pt.12 requires making visible controls actually do
 * something, or removing the affordance that implies they do. Aide now
 * opens a real (if minimal) help panel; the language indicator no longer
 * has a dropdown chevron since there is no second language to switch to.
 */
export function AppHeader({
  syncState = 'local',
  syncErrorMessage = null,
}: {
  syncState?: SyncState;
  syncErrorMessage?: string | null;
}) {
  const helpOpen = useUiStore((state) => state.helpOpen);
  const toggleHelp = useUiStore((state) => state.toggleHelp);
  const display = SYNC_STATE_DISPLAY[syncState];

  useEffect(() => {
    if (!helpOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') toggleHelp();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [helpOpen, toggleHelp]);

  return (
    <header className="relative flex items-center justify-between border-b border-border bg-surface px-8 py-4">
      <div className="flex items-baseline gap-3">
        <span className="text-lg font-semibold tracking-tight text-ink">GreenCube</span>
        <span className="text-sm text-ink-faint">Configurateur de besoin de refroidissement</span>
      </div>
      <div className="flex items-center gap-5 text-sm text-ink-soft">
        <span
          className={'flex items-center gap-1.5' + (syncState === 'error' ? ' text-red-600' : '')}
          title={syncState === 'error' && syncErrorMessage ? syncErrorMessage : undefined}
          aria-live="polite"
        >
          <span aria-hidden>{display.icon}</span>
          {display.label}
        </span>
        <button
          type="button"
          onClick={toggleHelp}
          aria-expanded={helpOpen}
          className="flex items-center gap-1.5 hover:text-ink"
        >
          <span aria-hidden>❓</span> Aide
        </button>
        <span className="flex items-center gap-1 font-medium text-ink" title="Interface disponible en français uniquement">
          FR
        </span>
      </div>

      {helpOpen && (
        <div
          role="dialog"
          aria-label="Aide"
          className="absolute right-8 top-full z-10 mt-2 w-80 rounded-xl border border-border bg-surface p-4 text-sm shadow-lg"
        >
          <p className="font-medium text-ink">Aide — configurateur GreenCube Cooling</p>
          <p className="mt-2 text-ink-soft">
            L'assistant vous guide en 7 étapes (localisation, modèle, orientation, usage, équipements,
            ventilation/confort, vérification) puis lance un calcul MERCURE côté Odoo pour dimensionner la
            puissance de refroidissement recommandée. Vos données sont poussées vers Odoo aux points de
            contrôle de chaque étape et lors du calcul.
          </p>
          <button type="button" onClick={toggleHelp} className="mt-3 text-xs font-medium text-brand-700 hover:underline">
            Fermer
          </button>
        </div>
      )}
    </header>
  );
}
