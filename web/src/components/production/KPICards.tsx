import React from 'react';
import { Factory, Check, X, Activity } from 'lucide-react';
import type { Metrics } from '../../types/snapshot';

interface KPICardsProps {
  metrics: Metrics | null;
  cycleTimeMs: number | null;
}

interface KPICardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  colorClass: string;
}

const KPICard = React.memo(function KPICard({
  icon,
  label,
  value,
  colorClass,
}: KPICardProps) {
  return (
    <div className="kpi-card">
      <div className={`kpi-icon ${colorClass}`}>{icon}</div>
      <div className="kpi-info">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
});

export const KPICards = React.memo(function KPICards({
  metrics,
  cycleTimeMs,
}: KPICardsProps) {
  return (
    <div className="kpi-container">
      <KPICard
        icon={<Factory size={22} />}
        label="Total Inspected"
        value={metrics?.total_parts ?? 0}
        colorClass="blue"
      />
      <KPICard
        icon={<Check size={22} />}
        label="Passed"
        value={metrics?.passed_parts ?? 0}
        colorClass="green"
      />
      <KPICard
        icon={<X size={22} />}
        label="Rejected"
        value={metrics?.rejected_parts ?? 0}
        colorClass="red"
      />
      <KPICard
        icon={<Activity size={22} />}
        label="Cycle Time"
        value={cycleTimeMs != null ? `${cycleTimeMs} ms` : '--'}
        colorClass="yellow"
      />
    </div>
  );
});
