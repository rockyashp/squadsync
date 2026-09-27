import React, { useState } from 'react';
import { adminApi } from '../../api/adminApi';
import { ShieldAlert, X, Send, CheckCircle2 } from 'lucide-react';

const REPORT_REASONS = [
  'Toxic Communication & Verbal Abuse',
  'Griefing & Match Throwing',
  'Cheating, Exploiting or Third-Party Tools',
  'Inappropriate Gamer Tag or Profile Content',
  'Harassment or Stalking',
  'Spamming / Advertising',
  'Other Conduct Violation'
];

function ReportUserModal({ isOpen, onClose, targetUser, onReportSubmitted }) {
  const [reason, setReason] = useState(REPORT_REASONS[0]);
  const [details, setDetails] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  if (!isOpen || !targetUser) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        reported_user_id: targetUser.id || targetUser.user_id,
        reason,
        details: details.trim() || null
      };

      const res = await adminApi.submitReport(payload);
      setSuccess(true);
      if (onReportSubmitted) {
        onReportSubmitted(res?.data || res);
      }
      setTimeout(() => {
        setSuccess(false);
        setDetails('');
        onClose();
      }, 1800);
    } catch (err) {
      console.error('Failed to submit conduct report:', err);
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to file report.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const targetName = targetUser.gamer_tag || targetUser.username || 'Player';

  return (
    <div className="modalOverlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div 
        className="modalContainer glassCard"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: '500px',
          textAlign: 'left'
        }}
      >
        <button 
          type="button" 
          className="modalCloseBtn"
          onClick={onClose}
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <ShieldAlert color="var(--rose)" size={22} />
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#ffffff', fontFamily: "'Space Grotesk', sans-serif" }}>
            Report Player Conduct (BR-6)
          </h3>
        </div>

        {success ? (
          <div style={{ textAlign: 'center', padding: '24px 16px' }}>
            <CheckCircle2 color="#10b981" size={38} style={{ marginBottom: '10px' }} />
            <h4 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, margin: '0 0 6px 0', fontFamily: "'Space Grotesk', sans-serif" }}>Report Submitted</h4>
            <p style={{ color: 'var(--text2)', fontSize: '13px', margin: 0 }}>
              Admins will review this report against community guidelines within the 48-hour SLA (BR-6).
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '12px 14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              borderLeft: '3px solid var(--rose)',
              marginBottom: '16px',
              fontSize: '13px',
              color: 'var(--text2)'
            }}>
              Reporting gamer: <strong style={{ color: '#ffffff' }}>{targetName}</strong>
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', marginTop: '4px' }}>
                Per Business Rule BR-2, networking will be restricted upon moderation review.
              </div>
            </div>

            {error && (
              <div style={{
                padding: '10px 14px',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.35)',
                borderRadius: 'var(--radius-buttons)',
                color: '#f87171',
                fontSize: '12px',
                marginBottom: '16px'
              }}>
                {error}
              </div>
            )}

            <div className="formGroup" style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
                VIOLATION CATEGORY *
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-buttons)',
                  padding: '10px 14px',
                  color: '#ffffff',
                  fontSize: '13px',
                  outline: 'none'
                }}
              >
                {REPORT_REASONS.map((r) => (
                  <option key={r} value={r} style={{ background: '#0d1321', color: '#ffffff' }}>{r}</option>
                ))}
              </select>
            </div>

            <div className="formGroup" style={{ marginBottom: '22px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
                INCIDENT DETAILS & CONTEXT
              </label>
              <textarea
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                rows={4}
                placeholder="Provide match context, chat remarks, or timestamps to aid administrative review..."
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-buttons)',
                  padding: '10px 14px',
                  color: '#ffffff',
                  fontSize: '13px',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={onClose}
                className="glassBtn"
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="primaryBtn"
                style={{ padding: '8px 20px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Send size={13} />
                <span>{isSubmitting ? 'Filing...' : 'Submit Report'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default ReportUserModal;
