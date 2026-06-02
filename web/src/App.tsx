import { useState, useEffect } from 'react';
import { SnapshotProvider } from './contexts/SnapshotContext';
import { useSnapshotContext } from './contexts/SnapshotContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ProductionPage } from './pages/ProductionPage';
import { TrainingPage } from './pages/TrainingPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { AdminPage } from './pages/AdminPage';
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
  | 'configurations';

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

  const token =
    window.localStorage.getItem('diskvision_token');

  const showLogin =
    authReady &&
    authEnabled &&
    !token;

  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <main className="main-content">
        <Header
          activeTab={activeTab}
          settingsTab={settingsTab}
        />

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