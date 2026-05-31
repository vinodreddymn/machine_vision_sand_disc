import React from 'react';
import type { DatasetStats } from '../../types/snapshot';

interface DatasetMetricsProps {
  dataset: DatasetStats | undefined;
}

export const DatasetMetrics = React.memo(function DatasetMetrics({
  dataset,
}: DatasetMetricsProps) {
  return (
    <div className="plc-telemetry-panel">
      <h2 style={{ margin: 0, fontSize: '15px', color: '#f8fafc' }}>
        Dataset Collection Statistics
      </h2>
      <div className="plc-telemetry-grid">
        <div className="plc-telemetry-item">
          <span>Good Samples</span>
          <strong>{dataset?.total_good ?? 0}</strong>
        </div>
        <div className="plc-telemetry-item">
          <span>Defect Samples</span>
          <strong>{dataset?.total_defective ?? 0}</strong>
        </div>
        <div className="plc-telemetry-item">
          <span>Operator Corrections</span>
          <strong style={{ color: '#fbbf24' }}>
            {dataset?.operator_corrections ?? 0}
          </strong>
        </div>
        <div className="plc-telemetry-item">
          <span>Accuracy Estimate</span>
          <strong style={{ color: '#34d399' }}>
            {dataset?.system_accuracy_estimate
              ? `${dataset.system_accuracy_estimate}%`
              : '0.00%'}
          </strong>
        </div>
      </div>
    </div>
  );
});
