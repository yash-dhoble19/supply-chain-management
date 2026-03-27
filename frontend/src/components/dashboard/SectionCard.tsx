import type { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function SectionCard({
  title,
  description,
  action,
  children,
  className = "",
}: SectionCardProps) {
  return (
    <section
      className={`rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm lg:p-8 ${className}`}
    >
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-xl font-bold text-on-surface">{title}</h3>
          {description ? <p className="text-sm text-on-surface-variant">{description}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
