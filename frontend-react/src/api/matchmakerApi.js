import apiClient from './client';

export const matchmakerApi = {
  generateDNA: async (surveyData) => {
    return apiClient.post('/dna/generate', surveyData);
  },

  getDNA: async () => {
    return apiClient.get('/dna');
  },

  evaluateTeam: async (payload) => {
    return apiClient.post('/matchmaking/evaluate-team', payload);
  },

  recommendSquad: async (targetPlayerIds) => {
    return apiClient.post('/squads/recommend', { target_player_ids: targetPlayerIds });
  },
};
