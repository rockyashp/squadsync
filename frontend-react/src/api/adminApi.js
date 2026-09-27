import apiClient from './client';

export const adminApi = {
  getAnalytics: async () => {
    return apiClient.get('/admin/analytics');
  },

  getUsers: async (query = null, limit = 50) => {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (limit) params.append('limit', limit.toString());
    const qs = params.toString();
    return apiClient.get(qs ? `/admin/users?${qs}` : '/admin/users');
  },

  updateUserStatus: async (userId, statusUpdate) => {
    return apiClient.put(`/admin/users/${userId}/status`, statusUpdate);
  },

  getReports: async (statusFilter = null) => {
    const qs = statusFilter ? `?status_filter=${statusFilter}` : '';
    return apiClient.get(`/admin/reports${qs}`);
  },

  updateReportStatus: async (reportId, newStatus) => {
    return apiClient.put(`/admin/reports/${reportId}/status`, { status: newStatus });
  },

  submitReport: async (reportData) => {
    return apiClient.post('/admin/reports', reportData);
  },
};
