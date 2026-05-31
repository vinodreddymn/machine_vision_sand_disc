import React from 'react';

interface DecisionDisplayProps {
  decision: string | null;
}

export const DecisionDisplay = React.memo(function DecisionDisplay({
  decision,
}: DecisionDisplayProps) {
  const cls = decision ? decision.toLowerCase() : 'waiting';
  const label = decision ?? 'WAITING FOR PART';

  return (
    <div className={`large-decision-display ${cls}`} aria-live="polite">
      {label}
    </div>
  );
});
