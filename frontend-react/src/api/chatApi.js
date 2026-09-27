import apiClient from './client';

export const chatApi = {
  getDirectHistory: async (otherUserId, limit = 50) => {
    return apiClient.get(`/chat/direct/${otherUserId}?limit=${limit}`);
  },

  getTeamHistory: async (teamId, limit = 50) => {
    return apiClient.get(`/chat/team/${teamId}?limit=${limit}`);
  },
};
