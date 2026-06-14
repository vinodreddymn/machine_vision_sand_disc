import { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { SnapshotProvider } from './contexts/SnapshotContext';
import { useSnapshotContext } from './contexts/SnapshotContext';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ProductionPage } from './pages/ProductionPage';
import { TrainingPage } from './pages/TrainingPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { AdminPage } from './pages/admin/AdminPage';
import { LoginModal } from './components/auth/LoginModal';
import { getAuthConfig } from './services/authService';
import { canAccess } from './utils/permissions';

// ─── Tab Types ────────────────────────────────────────────────────────────────

type Tab =
  | 'production'
  | 'training'
  | 'history'
  | 'system'
  | 'admin'
  | 'settings';

type SettingsTab =
  | 'calibration'
  | 'tolerances'
  | 'configurations'
  | 'camera';

// ─── Access Denied Component ──────────────────────────────────────────────────

function AccessDenied() {
  return (
    <div style={{ padding: '24px' }}>
      <div className="alert">
        <strong>Access Denied</strong>
        <div>
          You do not have permission to access this page.
        </div>
      </div>
    </div>
  );
}

// ─── Inner App ────────────────────────────────────────────────────────────────

function AppInner() {
  const [activeTab, setActiveTab] = useState<Tab>('production');
  const [settingsTab, setSettingsTab] =
    useState<SettingsTab>('calibration');
  const [authEnabled, setAuthEnabled] = useState(false);
  const [authReady, setAuthReady] = useState(false);
  const headerRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLDivElement>(null);

  const { error } = useSnapshotContext();

  const role =
    window.localStorage.getItem('diskvision_role') ??
    'viewer';

  useEffect(() => {
    let mounted = true;

    getAuthConfig()
      .then((cfg) => {
        if (!mounted) return;

        setAuthEnabled(cfg.auth_enabled);
        setAuthReady(true);
      })
      .catch(() => {
        if (!mounted) return;

        setAuthEnabled(false);
        setAuthReady(true);
      });

    return () => {
      mounted = false;
    };
  }, []);

  useLayoutEffect(() => {
    const root = document.documentElement;

    const updateWorkspaceHeight = () => {
      const headerHeight = headerRef.current?.offsetHeight ?? 0;
      const footerHeight = footerRef.current?.offsetHeight ?? 0;
      const viewportHeight = window.visualViewport?.height ?? window.innerHeight;
      const availableHeight = Math.max(
        0,
        Math.round(viewportHeight - headerHeight - footerHeight),
      );

      root.style.setProperty('--workspace-header-height', `${headerHeight}px`);
      root.style.setProperty('--workspace-footer-height', `${footerHeight}px`);
      root.style.setProperty('--workspace-content-height', `${availableHeight}px`);
    };

    const resizeObserver = new ResizeObserver(() => {
      window.requestAnimationFrame(updateWorkspaceHeight);
    });

    if (headerRef.current) {
      resizeObserver.observe(headerRef.current);
    }

    if (footerRef.current) {
      resizeObserver.observe(footerRef.current);
    }

    window.addEventListener('resize', updateWorkspaceHeight);
    window.visualViewport?.addEventListener('resize', updateWorkspaceHeight);
    window.visualViewport?.addEventListener('scroll', updateWorkspaceHeight);

    updateWorkspaceHeight();

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateWorkspaceHeight);
      window.visualViewport?.removeEventListener('resize', updateWorkspaceHeight);
      window.visualViewport?.removeEventListener('scroll', updateWorkspaceHeight);
    };
  }, []);

  const token =
    window.localStorage.getItem('diskvision_token');

  const showLogin =
    authReady &&
    authEnabled &&
    !token;

  return (
    <div className="app-container">
      <div ref={headerRef}>
        <Header
          activeTab={activeTab}
          settingsTab={settingsTab}
          onTabChange={setActiveTab}
        />
      </div>

      <div className="app-body">
        <main className="main-content">

        {error && (
          <div
            style={{
              padding: '0 24px',
              marginTop: '16px',
            }}
          >
            <div className="alert" role="alert">
              {error}
            </div>
          </div>
        )}

        <ErrorBoundary>
          {/* Production */}
          {activeTab === 'production' && (
            <ProductionPage />
          )}

          {/* Training */}
          {activeTab === 'training' &&
            (canAccess(role, 'training') ? (
              <TrainingPage />
            ) : (
              <AccessDenied />
            ))}

          {/* History */}
          {activeTab === 'history' && (
            <HistoryPage active />
          )}

          {/* System Health */}
          {activeTab === 'system' &&
            (canAccess(role, 'system') ? (
              <SystemHealthPage />
            ) : (
              <AccessDenied />
            ))}

          {/* Admin */}
          {activeTab === 'admin' &&
            (canAccess(role, 'admin') ? (
              <AdminPage />
            ) : (
              <AccessDenied />
            ))}

          {/* Settings */}
          {activeTab === 'settings' &&
            (canAccess(role, 'settings') ? (
              <SettingsPage
                active
                settingsTab={settingsTab}
                onSettingsTabChange={(tab) =>
                  setSettingsTab(tab)
                }
              />
            ) : (
              <AccessDenied />
            ))}
        </ErrorBoundary>
        </main>
      </div>
      
      <div ref={footerRef}>
        <Footer />
      </div>

      {showLogin && (
        <LoginModal
          onLoggedIn={() =>
            window.location.reload()
          }
        />
      )}
    </div>
  );
}

// ─── Root App ─────────────────────────────────────────────────────────────────

export function App() {
  return (
    <SnapshotProvider>
      <AppInner />
    </SnapshotProvider>
  );
}
