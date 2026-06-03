import React from 'react';

interface DecisionDisplayProps {
  decision: string | null;
  confirmationMode?: string | null;
}

export const DecisionDisplay = React.memo(function DecisionDisplay({
  decision,
  confirmationMode,
}: DecisionDisplayProps) {
  const cls = decision ? decision.toLowerCase() : 'waiting';
  const label = decision ?? 'WAITING FOR PART';
  const mode = confirmationMode ?? 'AUTO_ACCEPT';

  return (
    <div className={`large-decision-display ${cls}`} aria-live="polite">
      <div>{label}</div>
      <div style={{ marginTop: '10px', fontSize: '12px', opacity: 0.8, letterSpacing: 0 }}>
        {mode.replaceAll('_', ' ')}
      </div>
    </div>
  );
});
