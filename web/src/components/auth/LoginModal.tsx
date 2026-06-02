import { useCallback, useState } from 'react';
import { Lock } from 'lucide-react';
import { login } from '../../services/authService';

interface LoginModalProps {
  onLoggedIn: () => void;
}

export function LoginModal({
  onLoggedIn,
}: LoginModalProps) {
  const [username, setUsername] = useState('vinod');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = useCallback(async () => {
    setBusy(true);
    setError(null);

    try {
      const res = await login(username, password);

      console.log('Login Response:', res);

      if (!res.auth_enabled) {
        setError(
          'Authentication is disabled on the server.'
        );
        return;
      }

      if (!res.token) {
        setError('Login failed.');
        return;
      }

      const role = (
        res.role ?? 'OPERATOR'
      ).toUpperCase();

      window.localStorage.setItem(
        'diskvision_token',
        res.token
      );

      window.localStorage.setItem(
        'diskvision_role',
        role
      );

      localStorage.setItem(
        'diskvision_username',
        username
      );

      console.log('Stored Role:', role);

      onLoggedIn();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : String(err)
      );
    } finally {
      setBusy(false);
    }
  }, [username, password, onLoggedIn]);

  
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background:
          'linear-gradient(135deg, #0f172a 0%, #111827 50%, #1e293b 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '24px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          background: 'rgba(255,255,255,0.06)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '20px',
          padding: '32px',
          boxShadow:
            '0 20px 60px rgba(0,0,0,0.45)',
        }}
      >
        {/* Logo & Title */}
        <div
          style={{
            textAlign: 'center',
            marginBottom: '28px',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '18px',
              background:
                'linear-gradient(135deg,#2563eb,#06b6d4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}
          >
            <Lock size={32} color="white" />
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: '28px',
              fontWeight: 700,
            }}
          >
            ASHTECH
          </h1>

          <div
            style={{
              marginTop: '6px',
              opacity: 0.75,
              fontSize: '14px',
            }}
          >
            Machine Vision Suite
          </div>

          <div
            style={{
              marginTop: '12px',
              fontSize: '13px',
              opacity: 0.6,
            }}
          >
            Sign in to access inspection dashboards,
            training datasets, analytics and system
            administration.
          </div>
        </div>

        {error && (
          <div
            className="alert"
            style={{
              marginBottom: '20px',
            }}
          >
            {error}
          </div>
        )}

        {/* Username */}
        <div style={{ marginBottom: '18px' }}>
          <label
            style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            Username
          </label>

          <input
            value={username}
            onChange={(e) =>
              setUsername(e.target.value)
            }
            disabled={busy}
            placeholder="Enter username"
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: '10px',
              border:
                '1px solid rgba(255,255,255,0.12)',
              background:
                'rgba(255,255,255,0.04)',
            }}
          />
        </div>

        {/* Password */}
        <div style={{ marginBottom: '24px' }}>
          <label
            style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            Password
          </label>

          <input
            type="password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            disabled={busy}
            placeholder="Enter password"
            onKeyDown={(e) => {
              if (
                e.key === 'Enter' &&
                password
              ) {
                void handleSubmit();
              }
            }}
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: '10px',
              border:
                '1px solid rgba(255,255,255,0.12)',
              background:
                'rgba(255,255,255,0.04)',
            }}
          />
        </div>

        {/* Sign In Button */}
        <button
          onClick={() => void handleSubmit()}
          disabled={
            busy || !username || !password
          }
          style={{
            width: '100%',
            padding: '14px',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 700,
            cursor: 'pointer',
            background:
              'linear-gradient(135deg,#2563eb,#06b6d4)',
            color: 'white',
            fontSize: '15px',
          }}
        >
          {busy
            ? 'Authenticating...'
            : 'Sign In'}
        </button>

        {/* Footer */}
        <div
          style={{
            marginTop: '24px',
            textAlign: 'center',
            fontSize: '12px',
            opacity: 0.55,
          }}
        >
          Disk Vision Inspector • Version 1.0
        </div>
      </div>
    </div>
  );

}