import React, { useCallback } from 'react';
import { Check, X } from 'lucide-react';
import { postJson } from '../../services/apiService';
import { API } from '../../utils/constants';

interface LabelPanelProps {
  pendingLabel: boolean;
  runAction: (fn: () => Promise<unknown>) => Promise<void>;
}

export const LabelPanel = React.memo(function LabelPanel({
  pendingLabel,
  runAction,
}: LabelPanelProps) {
  const handleGood = useCallback(
    () =>
      runAction(() =>
        postJson(API.OPERATOR_LABEL, { station: 'S1', operator_label: 'GOOD' }),
      ),
    [runAction],
  );

  const handleDefective = useCallback(
    () =>
      runAction(() =>
        postJson(API.OPERATOR_LABEL, {
          station: 'S1',
          operator_label: 'DEFECTIVE',
        }),
      ),
    [runAction],
  );

  return (
    <div className="panel" style={{ background: '#11141b', border: '1px solid #232a36' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
        }}
      >
        <span>Operator Dataset Label Assignment</span>
        {pendingLabel ? (
          <strong style={{ color: '#fbbf24', fontSize: '12px' }}>
            PENDING CONFIRMATION
          </strong>
        ) : (
          <span style={{ color: '#64748b', fontSize: '12px' }}>Idle</span>
        )}
      </div>
      <div style={{ display: 'flex', gap: '12px' }}>
        <button
          id="btn-label-good"
          className="button good"
          style={{ flex: 1 }}
          disabled={!pendingLabel}
          onClick={handleGood}
        >
          <Check size={16} />
          Confirm Good (PASS)
        </button>
        <button
          id="btn-label-defective"
          className="button danger"
          style={{ flex: 1 }}
          disabled={!pendingLabel}
          onClick={handleDefective}
        >
          <X size={16} />
          Mark Defective (FAIL)
        </button>
      </div>
    </div>
  );
});
