import type { PropsWithChildren } from 'react';
import clsx from 'clsx';

type Tone = 'brand' | 'warn' | 'danger' | 'neutral';

const toneClasses: Record<Tone, string> = {
  brand: 'bg-brand-50 text-brand-700',
  warn: 'bg-warn-50 text-warn-700',
  danger: 'bg-danger-50 text-danger-700',
  neutral: 'bg-surface-muted text-ink-soft',
};

export function Badge({ tone = 'brand', children }: PropsWithChildren<{ tone?: Tone }>) {
  return (
    <span className={clsx('rounded-full px-2.5 py-1 text-xs font-medium', toneClasses[tone])}>{children}</span>
  );
}
