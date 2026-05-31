import { HistoryProvider } from '../contexts/HistoryContext';
import { HistoryFilters } from '../components/history/HistoryFilters';
import { HistoryTable } from '../components/history/HistoryTable';
import { InspectionDetails } from '../components/history/InspectionDetails';
import { ErrorBoundary } from '../components/common/ErrorBoundary';

interface HistoryPageProps {
  active: boolean;
}

export function HistoryPage({ active }: HistoryPageProps) {
  return (
    <HistoryProvider active={active}>
      <div className="history-page">
        <div className="history-table-container">
          <ErrorBoundary>
            <HistoryFilters />
            <HistoryTable />
          </ErrorBoundary>
        </div>
        <div>
          <ErrorBoundary>
            <InspectionDetails />
          </ErrorBoundary>
        </div>
      </div>
    </HistoryProvider>
  );
}
