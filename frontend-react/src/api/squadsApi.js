import apiClient from './client';

export const squadsApi = {
  getMySquads: async () => {
    return apiClient.get('/teams/my');
  },

  getSquadDetails: async (teamId) => {
    return apiClient.get(`/teams/${teamId}`);
  },

  createSquad: async (squadData) => {
    return apiClient.post('/teams', squadData);
  },

  inviteMember: async (teamId, inviteData) => {
    return apiClient.post(`/teams/${teamId}/invite`, inviteData);
  },

  removeMember: async (teamId, userId) => {
    return apiClient.delete(`/teams/${teamId}/members/${userId}`);
  },
};
