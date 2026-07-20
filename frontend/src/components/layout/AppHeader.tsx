/**
 * `syncState` must be passed explicitly by any page that knows whether the
 * current study has actually been pushed to Odoo — defaulting to a false
 * "Enregistré" claim before any sync happened was audit finding P0-04.
 */
export function AppHeader({ syncState = 'local' }: { syncState?: 'local' | 'synced' }) {
  return (
    <header className="flex items-center justify-between border-b border-border bg-surface px-8 py-4">
      <div className="flex items-baseline gap-3">
        <span className="text-lg font-semibold tracking-tight text-ink">GreenCube</span>
        <span className="text-sm text-ink-faint">Configurateur de besoin de refroidissement</span>
      </div>
      <div className="flex items-center gap-5 text-sm text-ink-soft">
        <span className="flex items-center gap-1.5">
          <span aria-hidden>{syncState === 'synced' ? '☁️' : '📝'}</span>
          {syncState === 'synced' ? 'Synchronisé avec Odoo' : 'Brouillon local'}
        </span>
        <span className="flex items-center gap-1.5">
          <span aria-hidden>❓</span> Aide
        </span>
        <span className="flex items-center gap-1 font-medium text-ink">FR ⌄</span>
      </div>
    </header>
  );
}
