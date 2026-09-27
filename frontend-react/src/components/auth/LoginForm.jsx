import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogIn, AlertCircle } from 'lucide-react';

export default function LoginForm() {
  const { login, setAuthModalMode } = useAuth();
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: '', message: '' });
    setIsSubmitting(true);

    try {
      await login(emailOrUsername, password);
    } catch (err) {
      setStatus({
        type: 'error',
        message: err.message || 'Invalid email or password.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ textAlign: 'left' }}>
      <h2 style={{ fontSize: '26px', marginBottom: '8px', color: '#fff' }}>Welcome Back</h2>
      <p style={{ color: 'var(--text2)', fontSize: '14px', marginBottom: '24px' }}>
        Log in to access your Gamer DNA™ & Squad Matchmaker.
      </p>

      {status.message && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 16px',
          borderRadius: 'var(--radius-md)',
          background: status.type === 'error' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(46, 213, 115, 0.15)',
          border: `1px solid ${status.type === 'error' ? 'var(--rose)' : '#2ed573'}`,
          color: status.type === 'error' ? 'var(--rose)' : '#2ed573',
          fontSize: '13px',
          marginBottom: '20px',
        }}>
          <AlertCircle size={16} />
          <span>{status.message}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="inputGroup">
          <label>Email Address or Username</label>
          <input
            type="text"
            required
            placeholder="gamer@squadsync.gg or GamerTag"
            value={emailOrUsername}
            onChange={(e) => setEmailOrUsername(e.target.value)}
          />
        </div>

        <div className="inputGroup">
          <label>Password</label>
          <input
            type="password"
            required
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="primaryBtn fullWidth"
          disabled={isSubmitting}
          style={{ marginTop: '12px', padding: '14px' }}
        >
          {isSubmitting ? (
            'Connecting to SquadSync...'
          ) : (
            <>
              <LogIn size={18} />
              Log In
            </>
          )}
        </button>
      </form>

      <p style={{ marginTop: '24px', textAlign: 'center', fontSize: '13px', color: 'var(--text2)' }}>
        Don't have an account?{' '}
        <button
          type="button"
          onClick={() => setAuthModalMode('register')}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--cyan)',
            fontWeight: 700,
            cursor: 'pointer',
            padding: 0,
            textDecoration: 'underline',
          }}
        >
          Register Free
        </button>
      </p>
    </div>
  );
}
