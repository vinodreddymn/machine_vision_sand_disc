import React from 'react';

interface DefectReportProps {
  defects: string[];
  title?: string;
  emptyMessage?: string;
}

export const DefectReport = React.memo(function DefectReport({
  defects,
  title = 'Detected Defect Report',
  emptyMessage = 'No defects reported on latest run.',
}: DefectReportProps) {
  return (
    <div className="panel" style={{ flex: 1 }}>
      <h2>{title}</h2>
      <div className="defect-list" style={{ marginTop: '12px' }}>
        {defects.length > 0 ? (
          defects.map((defect, index) => <span key={index}>{defect}</span>)
        ) : (
          <span
            style={{
              background: 'transparent',
              borderColor: 'transparent',
              color: '#64748b',
            }}
          >
            {emptyMessage}
          </span>
        )}
      </div>
    </div>
  );
});
