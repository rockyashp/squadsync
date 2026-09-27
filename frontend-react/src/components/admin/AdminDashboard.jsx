import React, { useState, useEffect, useCallback } from 'react';
import { adminApi } from '../../api/adminApi';
import { useAuth } from '../../context/AuthContext';
import {
  ShieldAlert,
  Users,
  Shield,
  Sparkles,
  Heart,
  AlertTriangle,
  Search,
  CheckCircle2,
  XCircle,
  Unlock,
  Clock,
  RefreshCw,
  UserCheck,
  FileCheck
} from 'lucide-react';

function calculateSlaStatus(createdAtStr) {
  if (!createdAtStr) return { label: 'Unknown', isOverdue: false, remainingHours: 48 };
  const created = new Date(createdAtStr).getTime();
  const now = Date.now();
  const elapsedHours = (now - created) / (1000 * 60 * 60);
  const remainingHours = Math.round(48 - elapsedHours);

  if (remainingHours <= 0) {
    return {
      label: `SLA Overdue (${Math.abs(remainingHours)}h late)`,
      isOverdue: true,
      remainingHours
    };
  }
  return {
    label: `${remainingHours}h remaining`,
    isOverdue: false,
    remainingHours
  };
}

function AdminDashboard() {
  const { isAdmin } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState('users'); // 'users' | 'reports'

  // Analytics
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  // User Management
  const [users, setUsers] = useState([]);
  const [userQuery, setUserQuery] = useState('');
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [updatingUserId, setUpdatingUserId] = useState(null);

  // Moderation Reports
  const [reports, setReports] = useState([]);
  const [statusFilter, setStatusFilter] = useState('PENDING'); // PENDING | ALL | RESOLVED | DISMISSED
  const [loadingReports, setLoadingReports] = useState(false);
  const [updatingReportId, setUpdatingReportId] = useState(null);

  // Global error/success notice
  const [notice, setNotice] = useState(null);

  // Fetch KPI Analytics
  const fetchAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    try {
      const res = await adminApi.getAnalytics();
      const data = res?.data || res;
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoadingAnalytics(false);
    }
  }, []);

  // Fetch Users
  const fetchUsers = useCallback(async (query = '') => {
    setLoadingUsers(true);
    try {
      const res = await adminApi.getUsers(query || null, 50);
      const userList = res?.data?.data || res?.data || (Array.isArray(res) ? res : []);
      setUsers(userList);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  // Fetch Reports
  const fetchReports = useCallback(async (filter = 'PENDING') => {
    setLoadingReports(true);
    try {
      const res = await adminApi.getReports(filter === 'ALL' ? null : filter);
      const reportList = res?.data?.data || res?.data || (Array.isArray(res) ? res : []);
      setReports(reportList);
    } catch (err) {
      console.error('Failed to load moderation reports:', err);
    } finally {
      setLoadingReports(false);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) {
      fetchAnalytics();
      fetchUsers();
      fetchReports();
    }
  }, [isAdmin, fetchAnalytics, fetchUsers, fetchReports]);

  const handleToggleUserStatus = async (user, field) => {
    setUpdatingUserId(user.id);
    try {
      const payload = {
        is_active: field === 'is_active' ? !user.is_active : user.is_active,
        is_locked: field === 'is_locked' ? !user.is_locked : user.is_locked
      };
      const res = await adminApi.updateUserStatus(user.id, payload);
      const updated = res?.data || res;
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, ...updated } : u));
      setNotice({ type: 'success', text: `Updated status for ${user.username}.` });
      fetchAnalytics();
    } catch (err) {
      console.error('Status update failed:', err);
      setNotice({ type: 'error', text: 'Failed to update user status.' });
    } finally {
      setUpdatingUserId(null);
      setTimeout(() => setNotice(null), 3000);
    }
  };

  const handleUpdateReportStatus = async (reportId, newStatus) => {
    setUpdatingReportId(reportId);
    try {
      const res = await adminApi.updateReportStatus(reportId, newStatus);
      const updated = res?.data || res;
      setReports(prev => prev.map(r => r.id === reportId ? { ...r, ...updated, status: newStatus } : r));
      setNotice({ type: 'success', text: `Report updated to ${newStatus}.` });
      fetchAnalytics();
    } catch (err) {
      console.error('Failed to update report:', err);
      setNotice({ type: 'error', text: 'Failed to update report resolution.' });
    } finally {
      setUpdatingReportId(null);
      setTimeout(() => setNotice(null), 3000);
    }
  };

  if (!isAdmin) {
    return (
      <div className="glassCard" style={{ padding: '60px 24px', textAlign: 'center', maxWidth: '600px', margin: '40px auto' }}>
        <ShieldAlert size={48} color="var(--rose)" style={{ marginBottom: '16px' }} />
        <h2 style={{ color: '#fff', fontSize: '20px', marginBottom: '8px', fontFamily: "'Space Grotesk', sans-serif" }}>Restricted Access (BR-4)</h2>
        <p style={{ color: 'var(--text2)', fontSize: '14px' }}>
          This console is strictly reserved for platform administrators.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'left' }}>
      {/* HEADER */}
      <div className="glassCard" style={{
        padding: '24px 28px',
        marginBottom: '24px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <ShieldAlert color="var(--cyan)" size={24} />
              <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
                Platform Administration & Moderation Console
              </h1>
              <span className="matchBadge">
                LEVEL 4 ROOT
              </span>
            </div>
            <p style={{ color: 'var(--text2)', margin: 0, fontSize: '13px' }}>
              Enforcing Community Guidelines, 48-Hour Conduct Resolution SLAs (BR-6), and Account State Moderation (BR-4).
            </p>
          </div>

          <button
            type="button"
            className="glassBtn"
            onClick={() => {
              fetchAnalytics();
              fetchUsers(userQuery);
              fetchReports(statusFilter);
            }}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', padding: '8px 16px' }}
          >
            <RefreshCw size={13} />
            <span>Refresh Telemetry</span>
          </button>
        </div>
      </div>

      {notice && (
        <div style={{
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '20px',
          background: notice.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          border: notice.type === 'success' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(244, 63, 94, 0.4)',
          color: notice.type === 'success' ? '#10b981' : '#f87171',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontFamily: "'Space Grotesk', sans-serif"
        }}>
          {notice.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          <span>{notice.text}</span>
        </div>
      )}

      {/* KPI METRIC CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
        gap: '14px',
        marginBottom: '24px'
      }}>
        <div className="glassCard" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL GAMERS</span>
            <Users size={16} color="var(--cyan)" />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
            {loadingAnalytics ? '...' : analytics?.total_users ?? 0}
          </h2>
        </div>

        <div className="glassCard" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', fontWeight: 600 }}>ACTIVE ACCOUNTS</span>
            <UserCheck size={16} color="#10b981" />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
            {loadingAnalytics ? '...' : analytics?.active_users ?? 0}
          </h2>
        </div>

        <div className="glassCard" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', fontWeight: 600 }}>ACTIVE SQUADS</span>
            <Shield size={16} color="var(--violet)" />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
            {loadingAnalytics ? '...' : analytics?.total_squads ?? 0}
          </h2>
        </div>

        <div className="glassCard" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', fontWeight: 600 }}>DNA SURVEYS</span>
            <Sparkles size={16} color="#facc15" />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
            {loadingAnalytics ? '...' : analytics?.total_surveys_completed ?? 0}
          </h2>
        </div>

        <div className="glassCard" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', fontWeight: 600 }}>FRIENDSHIPS</span>
            <Heart size={16} color="var(--rose)" />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
            {loadingAnalytics ? '...' : analytics?.total_friendships ?? 0}
          </h2>
        </div>

        <div className="glassCard" style={{
          padding: '18px 20px',
          borderColor: (analytics?.pending_reports || 0) > 0 ? 'rgba(244, 63, 94, 0.5)' : 'var(--border)',
          boxShadow: (analytics?.pending_reports || 0) > 0 ? '0 0 20px rgba(244, 63, 94, 0.2)' : 'none'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: (analytics?.pending_reports || 0) > 0 ? 'var(--rose)' : 'var(--text-muted)', fontWeight: 600 }}>
              PENDING TICKETS
            </span>
            <AlertTriangle size={16} color={(analytics?.pending_reports || 0) > 0 ? 'var(--rose)' : 'var(--text-muted)'} />
          </div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 700,
            color: (analytics?.pending_reports || 0) > 0 ? 'var(--rose)' : '#ffffff',
            margin: 0,
            fontFamily: "'Space Grotesk', sans-serif"
          }}>
            {loadingAnalytics ? '...' : analytics?.pending_reports ?? 0}
          </h2>
        </div>
      </div>

      {/* SUB-TABS NAVIGATION */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '14px' }}>
        <button
          type="button"
          onClick={() => setActiveSubTab('users')}
          style={{
            padding: '8px 16px',
            borderRadius: 'var(--radius-buttons)',
            fontSize: '13px',
            fontWeight: activeSubTab === 'users' ? 600 : 500,
            cursor: 'pointer',
            border: activeSubTab === 'users' ? '1px solid var(--cyan)' : '1px solid var(--border)',
            background: activeSubTab === 'users' ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.03)',
            color: activeSubTab === 'users' ? '#ffffff' : 'var(--text2)',
            boxShadow: activeSubTab === 'users' ? '0 0 15px rgba(34, 211, 238, 0.25)' : 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: "'Space Grotesk', sans-serif",
            transition: 'all var(--transition-fast)'
          }}
        >
          <Users size={15} color={activeSubTab === 'users' ? 'var(--cyan)' : 'currentColor'} />
          <span>User Accounts & Security ({users.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab('reports')}
          style={{
            padding: '8px 16px',
            borderRadius: 'var(--radius-buttons)',
            fontSize: '13px',
            fontWeight: activeSubTab === 'reports' ? 600 : 500,
            cursor: 'pointer',
            border: activeSubTab === 'reports' ? '1px solid var(--cyan)' : '1px solid var(--border)',
            background: activeSubTab === 'reports' ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.03)',
            color: activeSubTab === 'reports' ? '#ffffff' : 'var(--text2)',
            boxShadow: activeSubTab === 'reports' ? '0 0 15px rgba(34, 211, 238, 0.25)' : 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: "'Space Grotesk', sans-serif",
            transition: 'all var(--transition-fast)'
          }}
        >
          <AlertTriangle size={15} color={activeSubTab === 'reports' ? 'var(--cyan)' : 'currentColor'} />
          <span>Moderation Tickets (BR-6 SLA)</span>
          {(analytics?.pending_reports || 0) > 0 && (
            <span style={{
              background: 'rgba(244, 63, 94, 0.2)',
              border: '1px solid rgba(244, 63, 94, 0.4)',
              color: 'var(--rose)',
              fontSize: '10px',
              fontFamily: 'var(--font-geistmono)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-pills)',
              fontWeight: 700
            }}>
              {analytics.pending_reports}
            </span>
          )}
        </button>
      </div>

      {/* USER MANAGEMENT SECTION */}
      {activeSubTab === 'users' && (
        <div>
          {/* USER SEARCH */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <input
                type="text"
                value={userQuery}
                onChange={(e) => {
                  setUserQuery(e.target.value);
                  fetchUsers(e.target.value);
                }}
                placeholder="Search gamers by username or email..."
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-buttons)',
                  padding: '10px 14px 10px 38px',
                  color: '#ffffff',
                  fontSize: '13px',
                  outline: 'none',
                  transition: 'border-color var(--transition-fast)'
                }}
              />
              <Search
                size={16}
                color="var(--cyan)"
                style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }}
              />
            </div>
          </div>

          {/* USERS TABLE */}
          {loadingUsers ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div className="spinner" style={{ margin: '0 auto 12px' }}></div>
              <p style={{ color: 'var(--text2)', fontSize: '13px' }}>Loading accounts...</p>
            </div>
          ) : users.length === 0 ? (
            <div className="glassCard" style={{
              padding: '40px',
              textAlign: 'center',
            }}>
              <p style={{ color: 'var(--text2)', margin: 0, fontSize: '13px' }}>No user accounts found matching your query.</p>
            </div>
          ) : (
            <div className="glassCard" style={{
              overflowX: 'auto',
              padding: 0,
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)', background: 'rgba(255, 255, 255, 0.02)' }}>
                    <th style={{ padding: '12px 18px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>GAMER</th>
                    <th style={{ padding: '12px 18px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>EMAIL</th>
                    <th style={{ padding: '12px 18px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>ROLES</th>
                    <th style={{ padding: '12px 18px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>STATUS</th>
                    <th style={{ padding: '12px 18px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>SECURITY</th>
                    <th style={{ padding: '12px 18px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '11px', fontFamily: 'var(--font-geistmono)', textAlign: 'right' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => {
                    const isBusy = updatingUserId === u.id;
                    return (
                      <tr key={u.id} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '14px 18px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{
                              width: '32px',
                              height: '32px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(139, 92, 246, 0.2))',
                              border: '1px solid var(--border)',
                              color: '#ffffff',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '11px',
                              fontFamily: "'Space Grotesk', sans-serif"
                            }}>
                              {(u.gamer_tag || u.username).substring(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <strong style={{ color: '#ffffff', display: 'block', fontSize: '13px', fontWeight: 600, fontFamily: "'Space Grotesk', sans-serif" }}>{u.gamer_tag || u.username}</strong>
                              <span style={{ color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>@{u.username}</span>
                            </div>
                          </div>
                        </td>

                        <td style={{ padding: '14px 18px', color: 'var(--text2)', fontSize: '12px' }}>
                          {u.email}
                        </td>

                        <td style={{ padding: '14px 18px' }}>
                          {u.is_admin ? (
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-pills)',
                              fontSize: '10px',
                              fontFamily: 'var(--font-geistmono)',
                              fontWeight: 700,
                              background: 'rgba(244, 63, 94, 0.15)',
                              border: '1px solid rgba(244, 63, 94, 0.4)',
                              color: 'var(--rose)'
                            }}>
                              ADMIN
                            </span>
                          ) : (
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-pills)',
                              fontSize: '10px',
                              fontFamily: 'var(--font-geistmono)',
                              background: 'rgba(255, 255, 255, 0.05)',
                              border: '1px solid var(--border)',
                              color: 'var(--text2)'
                            }}>
                              GAMER
                            </span>
                          )}
                        </td>

                        <td style={{ padding: '14px 18px' }}>
                          {u.is_active ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#10b981', fontSize: '11px', fontFamily: 'var(--font-geistmono)', fontWeight: 600 }}>
                              <CheckCircle2 size={13} /> ACTIVE
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#f87171', fontSize: '11px', fontFamily: 'var(--font-geistmono)', fontWeight: 600 }}>
                              <XCircle size={13} /> SUSPENDED
                            </span>
                          )}
                        </td>

                        <td style={{ padding: '14px 18px' }}>
                          {u.is_locked ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#f87171', fontSize: '11px', fontFamily: 'var(--font-geistmono)', fontWeight: 600 }}>
                              LOCKED
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'var(--font-geistmono)' }}>
                              <Unlock size={12} /> NORMAL
                            </span>
                          )}
                        </td>

                        <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', gap: '8px' }}>
                            <button
                              type="button"
                              disabled={isBusy}
                              onClick={() => handleToggleUserStatus(u, 'is_active')}
                              className="glassBtn"
                              style={{
                                fontSize: '11px',
                                padding: '4px 10px',
                                color: u.is_active ? '#f87171' : '#10b981',
                                borderColor: u.is_active ? 'rgba(244, 63, 94, 0.4)' : 'rgba(16, 185, 129, 0.4)'
                              }}
                            >
                              {u.is_active ? 'Suspend' : 'Activate'}
                            </button>

                            <button
                              type="button"
                              disabled={isBusy}
                              onClick={() => handleToggleUserStatus(u, 'is_locked')}
                              className="glassBtn"
                              style={{
                                fontSize: '11px',
                                padding: '4px 10px',
                                color: u.is_locked ? '#10b981' : 'var(--text2)'
                              }}
                            >
                              {u.is_locked ? 'Unlock' : 'Lock'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* CONDUCT MODERATION REPORTS QUEUE */}
      {activeSubTab === 'reports' && (
        <div>
          {/* FILTER BAR */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              {['PENDING', 'ALL', 'RESOLVED', 'DISMISSED'].map((filter) => {
                const isSelected = statusFilter === filter;
                return (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => setStatusFilter(filter)}
                    style={{
                      padding: '4px 14px',
                      borderRadius: 'var(--radius-pills)',
                      fontSize: '11px',
                      fontFamily: 'var(--font-geistmono)',
                      fontWeight: isSelected ? 700 : 500,
                      cursor: 'pointer',
                      border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                      background: isSelected ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                      color: isSelected ? 'var(--cyan)' : 'var(--text2)',
                      boxShadow: isSelected ? '0 0 10px rgba(34, 211, 238, 0.2)' : 'none',
                      transition: 'all var(--transition-fast)'
                    }}
                  >
                    {filter}
                  </button>
                );
              })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)' }}>
              <Clock size={14} color="var(--cyan)" />
              <span>BR-6 48-Hour Resolution SLA</span>
            </div>
          </div>

          {loadingReports ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div className="spinner" style={{ margin: '0 auto 12px' }}></div>
              <p style={{ color: 'var(--text2)', fontSize: '13px' }}>Loading moderation queue...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="glassCard" style={{
              padding: '48px 24px',
              textAlign: 'center',
            }}>
              <FileCheck size={38} color="#10b981" style={{ marginBottom: '12px' }} />
              <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, marginBottom: '4px', fontFamily: "'Space Grotesk', sans-serif" }}>
                All Clear
              </h3>
              <p style={{ color: 'var(--text2)', fontSize: '13px', margin: 0 }}>
                No {statusFilter.toLowerCase()} moderation tickets currently in queue.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {reports.map((report) => {
                const sla = calculateSlaStatus(report.created_at);
                const isPending = report.status === 'PENDING';
                const isBusy = updatingReportId === report.id;

                return (
                  <div
                    key={report.id}
                    className="glassCard"
                    style={{
                      padding: '18px 22px',
                      borderLeft: isPending 
                        ? (sla.isOverdue ? '3px solid var(--rose)' : '3px solid #facc15')
                        : '3px solid #10b981'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '12px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', fontFamily: "'Space Grotesk', sans-serif" }}>
                            {report.reason}
                          </span>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-pills)',
                            fontSize: '10px',
                            fontFamily: 'var(--font-geistmono)',
                            fontWeight: 700,
                            background: isPending ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: isPending ? 'var(--rose)' : '#10b981',
                            border: isPending ? '1px solid rgba(244, 63, 94, 0.35)' : '1px solid rgba(16, 185, 129, 0.35)'
                          }}>
                            {report.status}
                          </span>
                        </div>

                        <div style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)' }}>
                          Ticket ID: <span style={{ color: '#ffffff' }}>{report.id}</span> • Reported user: <span style={{ color: '#ffffff' }}>{report.reported_user_id}</span>
                        </div>
                      </div>

                      {/* SLA BADGE */}
                      <div>
                        {isPending ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '4px 10px',
                            borderRadius: 'var(--radius-pills)',
                            fontSize: '11px',
                            fontFamily: 'var(--font-geistmono)',
                            fontWeight: 600,
                            background: sla.isOverdue ? 'rgba(244, 63, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                            color: sla.isOverdue ? 'var(--rose)' : '#facc15',
                            border: sla.isOverdue ? '1px solid rgba(244, 63, 94, 0.35)' : '1px solid rgba(234, 179, 8, 0.35)'
                          }}>
                            <Clock size={12} />
                            {sla.label}
                          </span>
                        ) : (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '4px 10px',
                            borderRadius: 'var(--radius-pills)',
                            fontSize: '11px',
                            fontFamily: 'var(--font-geistmono)',
                            fontWeight: 600,
                            background: 'rgba(16, 185, 129, 0.15)',
                            color: '#10b981',
                            border: '1px solid rgba(16, 185, 129, 0.35)'
                          }}>
                            <CheckCircle2 size={12} /> RESOLVED
                          </span>
                        )}
                      </div>
                    </div>

                    {report.details && (
                      <div style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '13px',
                        color: 'var(--text2)',
                        marginBottom: '14px',
                        border: '1px solid var(--border)',
                        lineHeight: 1.5
                      }}>
                        "{report.details}"
                      </div>
                    )}

                    {isPending && (
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => handleUpdateReportStatus(report.id, 'DISMISSED')}
                          className="glassBtn"
                          style={{ padding: '6px 14px', fontSize: '12px' }}
                        >
                          Dismiss Ticket
                        </button>
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => handleUpdateReportStatus(report.id, 'RESOLVED')}
                          className="primaryBtn"
                          style={{
                            padding: '6px 16px',
                            fontSize: '12px'
                          }}
                        >
                          Resolve & Moderate
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
