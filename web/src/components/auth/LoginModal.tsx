import { useCallback, useState } from 'react';
import { Lock } from 'lucide-react';
import { login } from '../../services/authService';

interface LoginModalProps {
  onLoggedIn: () => void;
}

export function LoginModal({ onLoggedIn }: LoginModalProps) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = useCallback(async () => {
    setBusy(true);
    try {
      const res = await login(username, password);
      if (!res.auth_enabled) {
        setError('Authentication is disabled on the server.');
        return;
      }
      if (!res.token) {
        setError('Login failed.');
        return;
      }
      window.localStorage.setItem('diskvision_token', res.token);
      setError(null);
      onLoggedIn();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, [username, password, onLoggedIn]);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15,18,25,0.86)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px',
    }}>
      <div className="settings-group" style={{ width: 'min(520px, 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Lock size={18} />
          <h2 style={{ margin: 0, fontSize: '16px' }}>Sign In</h2>
        </div>

        {error && <div className="alert">{error}</div>}

        <div className="settings-grid">
          <div className="settings-field">
            <label>Username</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div className="settings-field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="button good" onClick={handleSubmit} disabled={busy || !password}>
            {busy ? 'Signing in...' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}

