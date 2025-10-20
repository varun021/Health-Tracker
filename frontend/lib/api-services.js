import api from './axios-config';

export const userApi = {
  login: async (credentials) => {
    // Axios will send cookies automatically if backend sets them
    const response = await api.post('/api/users/login/', credentials);
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/api/users/register/', userData);
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/api/users/me/');
    return response.data;
  },

  updateProfile: async (userData) => {
    const response = await api.put('/api/users/me/', userData);
    return response.data;
  },

  logout: async () => {
    // Optional: add a logout endpoint that clears the HTTP-only cookie
    const response = await api.post('/api/users/logout/');
    return response.data;
  },

  predict: async (predictionData) => {
    const response = await api.post('/api/predictions/predict/', predictionData);
    return response.data;
  },

  getSymptoms: async () => {
    const response = await api.get('/api/symptoms/');
    return response.data;
  }
};
