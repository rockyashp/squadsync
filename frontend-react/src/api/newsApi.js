import apiClient from './client';

export const newsApi = {
  getNews: async (game = null, category = null, limit = 20) => {
    const params = new URLSearchParams();
    if (game && game !== 'All') params.append('game', game);
    if (category && category !== 'All') params.append('category', category);
    if (limit) params.append('limit', limit.toString());

    const qs = params.toString();
    return apiClient.get(qs ? `/news?${qs}` : '/news');
  },

  createArticle: async (articleData) => {
    return apiClient.post('/news', articleData);
  },
};
