import apiClient from './client';

export const authApi = {
  login: async (credentials) => {
    return apiClient.post('/auth/login', credentials);
  },

  register: async (userData) => {
    return apiClient.post('/auth/register', userData);
  },

  getMe: async () => {
    return apiClient.get('/auth/me');
  },

  logout: async () => {
    return apiClient.post('/auth/logout');
  },
};
