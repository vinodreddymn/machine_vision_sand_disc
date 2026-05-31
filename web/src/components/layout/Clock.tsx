import React from 'react';
import { formatDateTime } from '../../utils/dateUtils';

interface ClockProps {
  date: Date;
}

export const Clock = React.memo(function Clock({ date }: ClockProps) {
  return (
    <div className="header-clock" aria-label="System time">
      {formatDateTime(date)}
    </div>
  );
});
