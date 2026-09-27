import React, { useState, useEffect } from 'react';
import { friendsApi } from '../../api/friendsApi';
import { useAuth } from '../../context/AuthContext';
import FriendSearch from './FriendSearch';
import FriendCard from './FriendCard';
import PendingRequests from './PendingRequests';
import ReportUserModal from '../common/ReportUserModal';
import { Users, RefreshCw, Loader2, UserCheck } from 'lucide-react';

export default function FriendsHub({ onOpenChat }) {
  const { user } = useAuth();
  const [friends, setFriends] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [reportingUser, setReportingUser] = useState(null);

  const fetchSocialData = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    try {
      const [friendsRes, requestsRes] = await Promise.all([
        friendsApi.getFriends(),
        friendsApi.getPendingRequests(),
      ]);

      const friendsList = friendsRes.data?.data || friendsRes.data || [];
      const requestsList = requestsRes.data?.data || requestsRes.data || [];

      setFriends(friendsList);
      setPendingRequests(requestsList);
    } catch (err) {
      console.warn('Friends fetch warning:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSocialData();
  }, [user]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchSocialData();
  };

  const handleRequestHandled = (friendshipId, action) => {
    setPendingRequests((prev) => prev.filter((r) => r.friendship_id !== friendshipId));
    if (action === 'ACCEPT') {
      fetchSocialData();
    }
  };

  const handleFriendRemoved = (removedUserId) => {
    setFriends((prev) => prev.filter((f) => f.user_id !== removedUserId));
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'left' }}>
      {/* HEADER */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: 600, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
            Gamer Network & Social Hub
          </h2>
          <span className="matchBadge">
            COMMUNITY PROTOCOL
          </span>
        </div>
        <p style={{ color: 'var(--text2)', fontSize: '13px', margin: 0 }}>
          Discover competitive teammates, manage incoming invitations, and coordinate ranked lobbies.
        </p>
      </div>

      {!user ? (
        <div
          className="glassCard"
          style={{
            padding: '48px 24px',
            textAlign: 'center',
          }}
        >
          <Users size={36} color="var(--cyan)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, margin: '0 0 4px 0', fontFamily: "'Space Grotesk', sans-serif" }}>Authentication Required</h3>
          <p style={{ color: 'var(--text2)', fontSize: '13px', maxWidth: '420px', margin: '0 auto' }}>
            Sign in to view your friends list, discover teammates, and manage incoming invitations.
          </p>
        </div>
      ) : (
        /* TWO-COLUMN LAYOUT */
        <div className="friendsLayout">
          {/* LEFT COLUMN: SEARCH + CONFIRMED FRIENDS */}
          <div>
            {/* PLAYER DISCOVERY SEARCH */}
            <FriendSearch onRequestSent={fetchSocialData} />

            {/* CONFIRMED FRIENDS BAR */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', marginTop: '20px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', fontFamily: "'Space Grotesk', sans-serif" }}>
                <Users size={16} color="var(--cyan)" />
                Confirmed Friends ({friends.length})
              </h3>

              <button
                type="button"
                className="glassBtn"
                onClick={handleRefresh}
                disabled={refreshing}
                style={{ padding: '6px 14px', fontSize: '12px' }}
              >
                <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>

            {/* CONFIRMED FRIENDS GRID */}
            {loading ? (
              <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text2)' }}>
                <Loader2 size={28} className="animate-spin" color="var(--cyan)" style={{ margin: '0 auto 12px' }} />
                <p style={{ margin: 0, fontSize: '13px', fontFamily: 'var(--font-geistmono)' }}>Loading teammates...</p>
              </div>
            ) : friends.length === 0 ? (
              <div
                className="glassCard"
                style={{
                  padding: '40px 24px',
                  textAlign: 'center',
                }}
              >
                <Users size={32} color="var(--text2)" style={{ margin: '0 auto 12px' }} />
                <h4 style={{ color: '#ffffff', fontSize: '15px', fontWeight: 600, margin: '0 0 4px 0', fontFamily: "'Space Grotesk', sans-serif" }}>No Confirmed Friends Yet</h4>
                <p style={{ color: 'var(--text2)', fontSize: '13px', maxWidth: '400px', margin: '0 auto' }}>
                  Use the player search bar above to discover competitive gamers and expand your tactical network.
                </p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
                {friends.map((friend) => (
                  <FriendCard
                    key={friend.friendship_id || friend.user_id}
                    friend={friend}
                    onFriendRemoved={handleFriendRemoved}
                    onOpenChat={onOpenChat}
                    onReportPlayer={(target) => setReportingUser(target)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: PENDING INVITATIONS SIDEBAR */}
          <div>
            <PendingRequests
              requests={pendingRequests}
              onRequestHandled={handleRequestHandled}
            />
          </div>
        </div>
      )}

      {/* REPORT USER MODAL */}
      <ReportUserModal
        isOpen={!!reportingUser}
        onClose={() => setReportingUser(null)}
        targetUser={reportingUser}
      />
    </div>
  );
}
