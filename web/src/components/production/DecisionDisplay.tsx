import React from 'react';

interface DecisionDisplayProps {
  decision: string | null;
  confirmationMode?: string | null;
}

export const DecisionDisplay = React.memo(
  function DecisionDisplay({
    decision,
    confirmationMode,
  }: DecisionDisplayProps) {
    const state = decision
      ? decision.toLowerCase()
      : 'waiting';

    return (
      <div
        className={`decision-banner ${state}`}
      >
        <div className="decision-label">
          {decision ?? 'WAITING'}
        </div>

        <div className="decision-mode">
          {(confirmationMode ?? 'AUTO_ACCEPT')
            .replaceAll('_', ' ')}
        </div>
      </div>
    );
  }
);