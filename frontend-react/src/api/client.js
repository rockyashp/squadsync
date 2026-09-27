import axios from 'axios';

export const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatic JWT Bearer token injection
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('squadsync_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle ApiResponse envelopes and errors
apiClient.interceptors.response.use(
  (response) => {
    // If standard backend envelope { success: true, data: ..., message: ... }
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      console.warn('Session expired or unauthorized.');
    }
    const data = error.response?.data;
    let message = 'An unexpected network error occurred.';

    if (data?.errors?.[0]?.message) {
      message = data.errors[0].message;
    } else if (Array.isArray(data?.detail)) {
      message = data.detail
        .map((d) => (d.msg ? d.msg.replace(/^Value error,\s*/i, '') : typeof d === 'string' ? d : JSON.stringify(d)))
        .join('; ');
    } else if (typeof data?.detail === 'string') {
      message = data.detail;
    } else if (typeof data?.message === 'string') {
      message = data.message;
    } else if (error.message) {
      message = error.message;
    }

    return Promise.reject(new Error(message));
  }
);

export default apiClient;
