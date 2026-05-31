import React from 'react';
import { Database } from 'lucide-react';
import { useHistoryContext } from '../../contexts/HistoryContext';
import { DefectReport } from '../training/DefectReport';
import { API } from '../../utils/constants';

export const InspectionDetails = React.memo(function InspectionDetails() {
  const { selectedInspection } = useHistoryContext();

  if (!selectedInspection) {
    return (
      <div
        className="detail-inspector"
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%',
          minHeight: '300px',
          color: '#64748b',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <Database size={32} />
        <span>Select an inspection from the database log table to view details.</span>
      </div>
    );
  }

  const m = selectedInspection.measurements;

  return (
    <div className="detail-inspector">
      <div>
        <h2 style={{ margin: 0, fontSize: '16px' }}>Part Details Inspector</h2>
        <span style={{ fontSize: '12px', color: '#64748b' }}>
          ID: {selectedInspection.physical_part_id}
        </span>
      </div>

      {selectedInspection.overlay_path && (
        <div>
          <span
            style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}
          >
            Captured Image Overlay
          </span>
          <img
            src={`${API.IMAGE_OVERLAY}?t=${Date.now()}`}
            alt="Inspection Details"
          />
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {[
          ['Disposition', selectedInspection.final_disposition],
          ['Source Name', selectedInspection.source_name || '--'],
          ['Hole Count', m?.hole_count ?? '--'],
          [
            'Avg Hole Diam.',
            m?.avg_hole_diameter_px ? `${m.avg_hole_diameter_px} px` : '--',
          ],
          [
            'Defect Area Ratio',
            m?.surface_defect_area_ratio
              ? `${(Number(m.surface_defect_area_ratio) * 100).toFixed(2)}%`
              : '--',
          ],
        ].map(([label, value]) => (
          <div
            key={String(label)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              borderBottom: '1px solid #232a36',
              paddingBottom: '6px',
            }}
          >
            <span style={{ color: '#64748b' }}>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <DefectReport
        defects={selectedInspection.defects ?? []}
        title="Inspection Defect Report"
        emptyMessage="No defects detected."
      />
    </div>
  );
});
