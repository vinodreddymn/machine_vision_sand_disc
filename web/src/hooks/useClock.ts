import { useState, useEffect } from 'react';

/**
 * Provides a live-updating Date object, ticking every second.
 */
export function useClock(): Date {
  const [clock, setClock] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  return clock;
}
