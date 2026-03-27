import type { Metric, MetricTone } from "../../types/dashboard.types";
import { formatMetricValue } from "../../utils/formatters";

const toneStyles: Record<
  MetricTone,
  {
    rail: string;
    title: string;
    icon: string;
  }
> = {
  primary: {
    rail: "bg-primary",
    title: "text-on-secondary-container",
    icon: "text-primary",
  },
  danger: {
    rail: "bg-error",
    title: "text-error",
    icon: "text-error",
  },
  warning: {
    rail: "bg-tertiary",
    title: "text-tertiary",
    icon: "text-tertiary",
  },
  success: {
    rail: "bg-success",
    title: "text-success",
    icon: "text-success",
  },
  neutral: {
    rail: "bg-primary-container",
    title: "text-on-secondary-container",
    icon: "text-on-surface-variant",
  },
};

interface MetricCardProps {
  metric: Metric;
}

export function MetricCard({ metric }: MetricCardProps) {
  const style = toneStyles[metric.tone];

  return (
    <article className="group relative overflow-hidden rounded-xl bg-surface-container-lowest p-6 shadow-panel">
      <div className={`absolute left-0 top-0 h-full w-1 ${style.rail}`} />
      <div className="flex flex-col">
        <span className={`mb-2 text-[0.6875rem] font-semibold uppercase tracking-[0.2em] ${style.title}`}>
          {metric.title}
        </span>
        <span className="leading-none text-[2.25rem] font-bold text-on-primary-fixed">
          {formatMetricValue(metric)}
        </span>
        <div className={`mt-4 flex items-center gap-1 text-xs font-bold ${style.icon}`}>
          <span className="material-symbols-outlined text-base">{metric.icon}</span>
          <span>{metric.change || metric.status}</span>
        </div>
        <p className="mt-1 text-xs font-medium text-on-surface-variant">{metric.status}</p>
      </div>
    </article>
  );
}
