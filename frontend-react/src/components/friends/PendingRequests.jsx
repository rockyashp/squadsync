import React, { useState } from 'react';
import { Check, X, Bell, Loader2 } from 'lucide-react';
import { friendsApi } from '../../api/friendsApi';

export default function PendingRequests({ requests, onRequestHandled }) {
  const [actingMap, setActingMap] = useState({});

  const handleAction = async (friendshipId, action) => {
    setActingMap((prev) => ({ ...prev, [friendshipId]: action }));
    try {
      await friendsApi.respondToRequest(friendshipId, action);
      if (onRequestHandled) onRequestHandled(friendshipId, action);
    } catch (err) {
      alert(`Failed to ${action.toLowerCase()} friend request.`);
    } finally {
      setActingMap((prev) => ({ ...prev, [friendshipId]: null }));
    }
  };

  return (
    <div
      className="glassCard"
      style={{
        padding: '20px',
        textAlign: 'left'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', fontFamily: "'Space Grotesk', sans-serif" }}>
          <Bell size={15} color="var(--cyan)" />
          Pending Invitations
        </h3>
        <span
          className="matchBadge"
          style={{
            color: requests.length > 0 ? 'var(--cyan)' : 'var(--text-muted)',
            borderColor: requests.length > 0 ? 'var(--cyan)' : 'var(--border)',
            background: requests.length > 0 ? 'rgba(34, 211, 238, 0.15)' : 'transparent'
          }}
        >
          {requests.length}
        </span>
      </div>

      {requests.length === 0 ? (
        <p style={{ color: 'var(--text2)', fontSize: '12px', margin: 0, textAlign: 'center', padding: '16px 0', fontFamily: 'var(--font-geistmono)' }}>
          No pending friend invitations.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {requests.map((req) => {
            const isProcessing = !!actingMap[req.friendship_id];
            return (
              <div
                key={req.friendship_id}
                style={{
                  padding: '10px 14px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(139, 92, 246, 0.2))',
                      border: '1px solid var(--border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      color: '#ffffff',
                      fontSize: '11px',
                      fontFamily: "'Space Grotesk', sans-serif",
                      flexShrink: 0,
                    }}
                  >
                    {(req.sender_gamer_tag || req.sender_username || 'G').substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h5 style={{ color: '#ffffff', margin: '0 0 2px 0', fontSize: '13px', fontWeight: 600, fontFamily: "'Space Grotesk', sans-serif" }}>
                      {req.sender_gamer_tag || req.sender_username}
                    </h5>
                    {req.primary_role && (
                      <span style={{
                        fontSize: '10px',
                        fontFamily: 'var(--font-geistmono)',
                        padding: '2px 8px',
                        background: 'rgba(34, 211, 238, 0.1)',
                        borderRadius: 'var(--radius-pills)',
                        color: 'var(--cyan)',
                        border: '1px solid rgba(34, 211, 238, 0.25)'
                      }}>
                        {req.primary_role}
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    type="button"
                    className="glassBtn"
                    onClick={() => handleAction(req.friendship_id, 'ACCEPT')}
                    disabled={isProcessing}
                    title="Accept Friend Request"
                    style={{
                      padding: '5px 10px',
                      fontSize: '11px',
                      color: '#10b981',
                      border: '1px solid rgba(16, 185, 129, 0.4)'
                    }}
                  >
                    {actingMap[req.friendship_id] === 'ACCEPT' ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Check size={12} strokeWidth={2.5} />
                    )}
                  </button>

                  <button
                    type="button"
                    className="glassBtn"
                    onClick={() => handleAction(req.friendship_id, 'REJECT')}
                    disabled={isProcessing}
                    title="Decline Friend Request"
                    style={{
                      padding: '5px 10px',
                      fontSize: '11px',
                      color: '#f87171',
                      border: '1px solid rgba(248, 113, 113, 0.4)'
                    }}
                  >
                    {actingMap[req.friendship_id] === 'REJECT' ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <X size={12} />
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
