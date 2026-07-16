import type { ReactNode } from 'react';
import clsx from 'clsx';

interface StatTileProps {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  valueClassName?: string;
}

export function StatTile({ icon, label, value, valueClassName }: StatTileProps) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-xl border border-border bg-surface px-3 py-4 text-center">
      <div className="text-brand-600">{icon}</div>
      <div className="text-xs text-ink-soft">{label}</div>
      <div className={clsx('text-sm font-semibold text-ink', valueClassName)}>{value}</div>
    </div>
  );
}
