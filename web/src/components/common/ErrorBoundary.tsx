import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches any JavaScript errors in the component tree below it.
 * Displays a fallback UI instead of crashing the whole app.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '48px',
            gap: '16px',
            color: '#ef4444',
            textAlign: 'center',
          }}
        >
          <AlertTriangle size={40} />
          <h2 style={{ margin: 0, color: '#f8fafc' }}>Something went wrong</h2>
          <p style={{ margin: 0, color: '#94a3b8', maxWidth: '480px', fontSize: '14px' }}>
            {this.state.error?.message ?? 'An unexpected error occurred in this section.'}
          </p>
          <button className="button" onClick={this.handleReset}>
            <RefreshCcw size={14} />
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
