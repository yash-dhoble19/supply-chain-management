import type { Activity, ActivityType } from "../../types/dashboard.types";
import { formatRelativeTime, getActivityAriaLabel } from "../../utils/formatters";

const activityStyles: Record<
  ActivityType,
  {
    wrapper: string;
    icon: string;
    iconName: string;
  }
> = {
  inventory: {
    wrapper: "bg-blue-100",
    icon: "text-blue-600",
    iconName: "inventory_2",
  },
  procurement: {
    wrapper: "bg-amber-100",
    icon: "text-amber-600",
    iconName: "receipt_long",
  },
  shipment: {
    wrapper: "bg-green-100",
    icon: "text-green-600",
    iconName: "local_shipping",
  },
  order: {
    wrapper: "bg-purple-100",
    icon: "text-purple-600",
    iconName: "shopping_bag",
  },
};

interface ActivityItemProps {
  activity: Activity;
}

export function ActivityItem({ activity }: ActivityItemProps) {
  const style = activityStyles[activity.type];

  return (
    <article className="flex gap-4" aria-label={getActivityAriaLabel(activity)}>
      <div className="mt-1">
        <div className={`flex h-8 w-8 items-center justify-center rounded-full ${style.wrapper}`}>
          <span className={`material-symbols-outlined text-sm ${style.icon}`}>{style.iconName}</span>
        </div>
      </div>
      <div>
        <p className="text-sm font-semibold text-on-surface">{activity.title}</p>
        <p className="text-xs text-on-surface-variant">{activity.description}</p>
        <p className="mt-1 text-xs font-medium text-on-secondary-container">
          {formatRelativeTime(activity.timestamp)}
        </p>
      </div>
    </article>
  );
}
