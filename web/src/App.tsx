import { useState } from 'react';
import { useEffect } from 'react';
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
import { LoginModal } from './components/auth/LoginModal';
import { getAuthConfig } from './services/authService';

// ─── Tab Types ────────────────────────────────────────────────────────────────

type Tab = 'production' | 'training' | 'history' | 'system' | 'settings';
type SettingsTab = 'calibration' | 'tolerances';

// ─── Inner App (needs to be inside SnapshotProvider) ─────────────────────────

function AppInner() {
  const [activeTab, setActiveTab] = useState<Tab>('production');
  const [settingsTab, setSettingsTab] = useState<SettingsTab>('calibration');
  const [authEnabled, setAuthEnabled] = useState(false);
  const [authReady, setAuthReady] = useState(false);
  const { error } = useSnapshotContext();

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
    return () => { mounted = false; };
  }, []);

  const token = window.localStorage.getItem('diskvision_token');
  const showLogin = authReady && authEnabled && !token;

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="main-content">
        <Header activeTab={activeTab} settingsTab={settingsTab} />

        {error && (
          <div style={{ padding: '0 24px', marginTop: '16px' }}>
            <div className="alert" role="alert">
              {error}
            </div>
          </div>
        )}

        <ErrorBoundary>
          {activeTab === 'production' && <ProductionPage />}
          {activeTab === 'training' && <TrainingPage />}
          {activeTab === 'history' && (
            <HistoryPage active={activeTab === 'history'} />
          )}
          {activeTab === 'system' && <SystemHealthPage />}
          {activeTab === 'settings' && (
            <SettingsPage
              active={activeTab === 'settings'}
              settingsTab={settingsTab}
              onSettingsTabChange={setSettingsTab}
            />
          )}
        </ErrorBoundary>
      </main>

      {showLogin && <LoginModal onLoggedIn={() => window.location.reload()} />}
    </div>
  );
}

// ─── Root App — wraps SnapshotProvider ───────────────────────────────────────

export function App() {
  return (
    <SnapshotProvider>
      <AppInner />
    </SnapshotProvider>
  );
}
