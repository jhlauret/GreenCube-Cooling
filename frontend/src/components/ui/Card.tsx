import type { PropsWithChildren, ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps {
  title?: ReactNode;
  action?: ReactNode;
  className?: string;
  padded?: boolean;
}

export function Card({ title, action, className, padded = true, children }: PropsWithChildren<CardProps>) {
  return (
    <section className={clsx('rounded-2xl border border-border bg-surface', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between px-6 pt-5">
          {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
          {action}
        </div>
      )}
      <div className={padded ? 'p-6' : undefined}>{children}</div>
    </section>
  );
}
