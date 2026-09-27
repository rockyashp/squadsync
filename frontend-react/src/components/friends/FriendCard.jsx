import React, { useState } from 'react';
import { UserMinus, MessageSquare, Shield } from 'lucide-react';
import { friendsApi } from '../../api/friendsApi';

export default function FriendCard({ friend, onFriendRemoved, onOpenChat, onReportPlayer }) {
  const [removing, setRemoving] = useState(false);

  const handleRemove = async () => {
    if (!window.confirm(`Are you sure you want to remove ${friend.gamer_tag || friend.username} from your friends list?`)) {
      return;
    }

    setRemoving(true);
    try {
      await friendsApi.removeFriend(friend.user_id);
      if (onFriendRemoved) onFriendRemoved(friend.user_id);
    } catch (err) {
      alert('Failed to remove friend.');
    } finally {
      setRemoving(false);
    }
  };

  const isOnline = friend.is_online !== false;

  return (
    <div
      className="glassCard"
      style={{
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        transition: 'all var(--transition-fast)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* AVATAR WITH ONLINE STATUS */}
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: 'var(--radius-sm)',
          background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(139, 92, 246, 0.2))',
          border: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: 700,
          color: '#ffffff',
          fontFamily: "'Space Grotesk', sans-serif",
          position: 'relative'
        }}>
          {(friend.gamer_tag || friend.username || 'G').substring(0, 2).toUpperCase()}
          <span style={{
            position: 'absolute',
            bottom: '-2px',
            right: '-2px',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isOnline ? '#10b981' : '#64748b',
            border: '1.5px solid #060911',
            boxShadow: isOnline ? '0 0 8px rgba(16, 185, 129, 0.8)' : 'none'
          }} />
        </div>

        {/* METADATA */}
        <div style={{ textAlign: 'left' }}>
          <h4 style={{ margin: '0 0 3px 0', fontSize: '14px', fontWeight: 600, color: '#ffffff', fontFamily: "'Space Grotesk', sans-serif" }}>
            {friend.gamer_tag || friend.username}
          </h4>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <span style={{
              fontSize: '10px',
              fontFamily: 'var(--font-geistmono)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-pills)',
              background: 'rgba(34, 211, 238, 0.1)',
              border: '1px solid rgba(34, 211, 238, 0.25)',
              color: 'var(--cyan)'
            }}>
              {friend.primary_role || 'Flex'}
            </span>
            {friend.rank_tier && (
              <span style={{ fontSize: '11px', color: 'var(--text2)', fontFamily: 'var(--font-geistmono)' }}>
                • {friend.rank_tier}
              </span>
            )}
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: isOnline ? '#10b981' : 'var(--text-muted)' }}>
              • {isOnline ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>

      {/* ACTIONS */}
      <div style={{ display: 'flex', gap: '6px' }}>
        {onOpenChat && (
          <button
            type="button"
            className="glassBtn"
            onClick={() => onOpenChat({
              type: 'direct',
              id: friend.user_id,
              name: friend.gamer_tag || friend.username,
              role: friend.primary_role || 'Flex',
              isOnline
            })}
            title="Chat with Friend"
            style={{ padding: '6px 10px', fontSize: '12px' }}
          >
            <MessageSquare size={13} color="var(--cyan)" />
          </button>
        )}

        {onReportPlayer && (
          <button
            type="button"
            className="glassBtn"
            onClick={() => onReportPlayer(friend)}
            title="Report Player Conduct (BR-6)"
            style={{ padding: '6px 10px', fontSize: '12px', color: 'var(--rose)' }}
          >
            <Shield size={13} />
          </button>
        )}

        <button
          type="button"
          className="glassBtn"
          onClick={handleRemove}
          disabled={removing}
          title="Remove Friend"
          style={{ padding: '6px 10px', fontSize: '12px', color: '#f87171' }}
        >
          <UserMinus size={13} />
        </button>
      </div>
    </div>
  );
}
