import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserPlus, AlertCircle } from 'lucide-react';

export default function RegisterForm() {
  const { register, setAuthModalMode } = useAuth();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    gamerTag: '',
    preferredGame: 'VALORANT',
    email: '',
    password: '',
  });
  const [status, setStatus] = useState({ type: '', message: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const passwordCriteria = {
    length: formData.password.length >= 8,
    upper: /[A-Z]/.test(formData.password),
    lower: /[a-z]/.test(formData.password),
    digit: /\d/.test(formData.password),
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(formData.password),
  };

  const isPasswordValid = 
    passwordCriteria.length &&
    passwordCriteria.upper &&
    passwordCriteria.lower &&
    passwordCriteria.digit &&
    passwordCriteria.special;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: '', message: '' });

    if (!passwordCriteria.length) {
      setStatus({ type: 'error', message: 'Password must be at least 8 characters long.' });
      return;
    }
    if (!passwordCriteria.upper) {
      setStatus({ type: 'error', message: 'Password must contain at least one uppercase letter (A-Z).' });
      return;
    }
    if (!passwordCriteria.lower) {
      setStatus({ type: 'error', message: 'Password must contain at least one lowercase letter (a-z).' });
      return;
    }
    if (!passwordCriteria.digit) {
      setStatus({ type: 'error', message: 'Password must contain at least one number (0-9).' });
      return;
    }
    if (!passwordCriteria.special) {
      setStatus({ type: 'error', message: 'Password must contain at least one special symbol (!@#$%^&*).' });
      return;
    }

    setIsSubmitting(true);

    try {
      // Clean username from gamer tag for backend uniqueness
      const cleanUsername = formData.gamerTag.replace(/[^a-zA-Z0-9_-]/g, '_') || 'gamer_' + Math.floor(Math.random() * 1000);

      await register({
        username: cleanUsername,
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
        preferred_game: formData.preferredGame,
      });
    } catch (err) {
      setStatus({
        type: 'error',
        message: err.message || 'Registration failed. Email or username may already be registered.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ textAlign: 'left' }}>
      <h2 style={{ fontSize: '26px', marginBottom: '8px', color: '#fff', fontFamily: "'Space Grotesk', sans-serif" }}>Join Squad Sync</h2>
      <p style={{ color: 'var(--text2)', fontSize: '14px', marginBottom: '24px' }}>
        Create your profile to unleash AI-powered matchmaking.
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
        <div className="inputRow">
          <div className="inputGroup">
            <label>First Name</label>
            <input
              type="text"
              name="firstName"
              required
              placeholder="Alex"
              value={formData.firstName}
              onChange={handleChange}
            />
          </div>
          <div className="inputGroup">
            <label>Last Name</label>
            <input
              type="text"
              name="lastName"
              required
              placeholder="Vance"
              value={formData.lastName}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="inputRow">
          <div className="inputGroup">
            <label>Gamer Tag</label>
            <input
              type="text"
              name="gamerTag"
              required
              placeholder="Ghost_X"
              value={formData.gamerTag}
              onChange={handleChange}
            />
          </div>
          <div className="inputGroup">
            <label>Preferred Game</label>
            <select
              name="preferredGame"
              value={formData.preferredGame}
              onChange={handleChange}
            >
              <option value="VALORANT">VALORANT</option>
              <option value="Apex Legends">Apex Legends</option>
              <option value="CS2">Counter Strike 2</option>
              <option value="Rainbow Six">Rainbow Six Siege</option>
              <option value="COD">Call of Duty</option>
            </select>
          </div>
        </div>

        <div className="inputGroup">
          <label>Email Address</label>
          <input
            type="email"
            name="email"
            required
            placeholder="gamer@squadsync.gg"
            value={formData.email}
            onChange={handleChange}
          />
        </div>

        <div className="inputGroup" style={{ marginBottom: '14px' }}>
          <label>Password (Min. 8 characters)</label>
          <input
            type="password"
            name="password"
            required
            placeholder="••••••••"
            value={formData.password}
            onChange={handleChange}
          />
          {formData.password && (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '6px 12px',
              marginTop: '8px',
              fontSize: '11px',
              fontFamily: "'Space Grotesk', sans-serif"
            }}>
              <span style={{ color: passwordCriteria.length ? '#10b981' : '#64748b' }}>
                {passwordCriteria.length ? '✓' : '○'} 8+ Chars
              </span>
              <span style={{ color: passwordCriteria.upper ? '#10b981' : '#64748b' }}>
                {passwordCriteria.upper ? '✓' : '○'} Uppercase
              </span>
              <span style={{ color: passwordCriteria.lower ? '#10b981' : '#64748b' }}>
                {passwordCriteria.lower ? '✓' : '○'} Lowercase
              </span>
              <span style={{ color: passwordCriteria.digit ? '#10b981' : '#64748b' }}>
                {passwordCriteria.digit ? '✓' : '○'} Number
              </span>
              <span style={{ color: passwordCriteria.special ? '#10b981' : '#64748b' }}>
                {passwordCriteria.special ? '✓' : '○'} Special (!@#$)
              </span>
            </div>
          )}
        </div>

        <button
          type="submit"
          className="primaryBtn fullWidth"
          disabled={isSubmitting}
          style={{ marginTop: '12px', padding: '14px' }}
        >
          {isSubmitting ? (
            'Creating Profile...'
          ) : (
            <>
              <UserPlus size={18} />
              Create Profile
            </>
          )}
        </button>
      </form>

      <p style={{ marginTop: '24px', textAlign: 'center', fontSize: '13px', color: 'var(--text2)' }}>
        Already have an account?{' '}
        <button
          type="button"
          onClick={() => setAuthModalMode('login')}
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
          Log In
        </button>
      </p>
    </div>
  );
}
