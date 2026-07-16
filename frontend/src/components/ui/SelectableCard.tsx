import type { PropsWithChildren, ReactNode } from 'react';
import clsx from 'clsx';

interface SelectableCardProps {
  selected: boolean;
  onClick: () => void;
  icon?: ReactNode;
  label: string;
  description?: string;
  className?: string;
}

export function SelectableCard({
  selected,
  onClick,
  icon,
  label,
  description,
  className,
  children,
}: PropsWithChildren<SelectableCardProps>) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={clsx(
        'relative flex flex-col items-center gap-2 rounded-xl border px-4 py-4 text-center transition-colors',
        selected ? 'border-brand-500 bg-brand-50' : 'border-border bg-surface hover:border-brand-300',
        className,
      )}
    >
      {selected && (
        <span className="absolute left-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-brand-600 text-[10px] text-white">
          ✓
        </span>
      )}
      {icon && <div className="text-2xl text-ink">{icon}</div>}
      <div className="text-sm font-medium text-ink">{label}</div>
      {description && <div className="text-xs text-ink-soft">{description}</div>}
      {children}
    </button>
  );
}
