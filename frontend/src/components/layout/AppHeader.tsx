export function AppHeader() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-surface px-8 py-4">
      <div className="flex items-baseline gap-3">
        <span className="text-lg font-semibold tracking-tight text-ink">GreenCube</span>
        <span className="text-sm text-ink-faint">Configurateur de besoin de refroidissement</span>
      </div>
      <div className="flex items-center gap-5 text-sm text-ink-soft">
        <span className="flex items-center gap-1.5">
          <span aria-hidden>💾</span> Enregistré
        </span>
        <span className="flex items-center gap-1.5">
          <span aria-hidden>❓</span> Aide
        </span>
        <span className="flex items-center gap-1 font-medium text-ink">FR ⌄</span>
      </div>
    </header>
  );
}
