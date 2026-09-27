import apiClient from './client';

export const friendsApi = {
  getFriends: async () => {
    return apiClient.get('/friends');
  },

  getPendingRequests: async () => {
    return apiClient.get('/friends/requests');
  },

  searchGamers: async (query) => {
    return apiClient.get(`/friends/search?q=${encodeURIComponent(query)}`);
  },

  sendFriendRequest: async (targetUserId) => {
    return apiClient.post(`/friends/request/${targetUserId}`);
  },

  respondToRequest: async (requestId, action) => {
    return apiClient.put(`/friends/request/${requestId}`, { action: action.toUpperCase() });
  },

  removeFriend: async (friendUserId) => {
    return apiClient.delete(`/friends/${friendUserId}`);
  },
};
