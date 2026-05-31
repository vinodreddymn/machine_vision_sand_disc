import type { ReactNode } from 'react';

type HealthLevel = 'normal' | 'warning' | 'critical' | 'emergency';

interface StatusBadgeProps {
  label: string;
  value: string;
  level: HealthLevel;
  icon?: ReactNode;
}

export function StatusBadge({ label, value, level, icon }: StatusBadgeProps) {
  return (
    <div className={`sys-status-badge sys-${level}`}>
      <div className="sys-status-head">
        {icon}
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
    </div>
  );
}
