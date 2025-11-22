// import api from './axios-config';

// export const userApi = {
//   login: async (credentials) => {
//     // Axios will send cookies automatically if backend sets them
//     const response = await api.post('/api/users/login/', credentials);
//     return response.data;
//   },

//   register: async (userData) => {
//     const response = await api.post('/api/users/register/', userData);
//     return response.data;
//   },

//   getProfile: async () => {
//     const response = await api.get('/api/users/me/');
//     return response.data;
//   },

//   updateProfile: async (userData) => {
//     const response = await api.put('/api/users/me/', userData);
//     return response.data;
//   },

//   logout: async () => {
//     // Optional: add a logout endpoint that clears the HTTP-only cookie
//     const response = await api.post('/api/users/logout/');
//     return response.data;
//   },

//   predict: async (predictionData) => {
//     const response = await api.post('/api/predictions/predict/', predictionData);
//     return response.data;
//   },

//   getSymptoms: async () => {
//     const response = await api.get('/api/symptoms/');
//     return response.data;
//   }
// };

import api from './axios-config';

export const userApi = {
  // =========================
  // AUTHENTICATION
  // =========================
  login: async (credentials) => {
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
    const response = await api.post('/api/users/logout/');
    return response.data;
  },

  // =========================
  // DISEASE MANAGEMENT
  // =========================
  getDiseases: async () => {
    const response = await api.get('/api/diseases/');
    return response.data;
  },

  getDiseaseById: async (id) => {
    const response = await api.get(`/api/diseases/${id}/`);
    return response.data;
  },

  // =========================
  // SYMPTOM MANAGEMENT
  // =========================
  getSymptoms: async () => {
    const response = await api.get('/api/symptoms/');
    return response.data;
  },

  // =========================
  // PREDICTION SYSTEM
  // =========================
  predict: async (predictionData) => {
    const response = await api.post('/api/predictions/predict/', predictionData);
    return response.data;
  },

  getPredictionHistory: async (page = 1, pageSize = 20) => {
    const response = await api.get(
      `/api/predictions/history/?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },

  deleteHistory: async (id) => {
    const response = await api.delete(`/api/predictions/delete_history/${id}/`);
    return response.data;
  },

  // =========================
  // ANALYTICS & REPORTS
  // =========================
  getAnalytics: async (days = 30) => {
    const response = await api.get(`/api/predictions/analytics/?days=${days}`);
    return response.data;
  },

  getComparisonReport: async () => {
    const response = await api.get('/api/predictions/comparison_report/');
    return response.data;
  },

  getRecommendationsBasedOnHistory: async () => {
    const response = await api.get('/api/predictions/recommendations_based_on_history/');
    return response.data;
  },

  exportData: async (format = 'json') => {
    const response = await api.get(`/api/predictions/export_data/?format=${format}`, {
      responseType: format === 'csv' ? 'blob' : 'json',
    });
    return response.data;
  },

  generateReport: async (options) => {
    const {
      start_date,
      end_date,
      format = 'pdf',
      include_personal_info = true,
      include_recommendations = true,
    } = options;

    const response = await api.post(
      '/api/predictions/generate_report/',
      {
        start_date,
        end_date,
        format,
        include_personal_info,
        include_recommendations,
      },
      {
        responseType: format === 'pdf' || format === 'csv' ? 'blob' : 'json',
      }
    );

    return response.data;
  },

  // =========================
  // MACHINE LEARNING
  // =========================
  trainModel: async () => {
    const response = await api.post('/api/predictions/train_model/');
    return response.data;
  },

  importDataset: async () => {
    const response = await api.post('/api/predictions/import_dataset/');
    return response.data;
  },

  getModelSummary: async () => {
    const [diseasesRes, symptomsRes, historyRes] = await Promise.all([
      api.get('/api/diseases/'),
      api.get('/api/symptoms/'),
      api.get('/api/predictions/history/?page=1&page_size=1'),
    ]);

    return {
      diseases: diseasesRes.data.length,
      symptoms: symptomsRes.data.length,
      samples_trained: historyRes.data.count,
    };
  },

  // =========================
  // CHAT ASSISTANT
  // =========================
  sendChatMessage: async (payload) => {
    const response = await api.post("/api/chat/send/", payload);
    return response.data;
  },

  getChatHistory: async () => {
    const response = await api.get("/api/chat/history/");
    return response.data;
  },

  getChatSummary: async () => {
    const response = await api.get("/api/chat/summary/");
    return response.data;
  },

  restartChat: async (hardDelete = false) => {
    const response = await api.post("/api/chat/restart/", { hard_delete: hardDelete });
    return response.data;
  },

  geminiChat: async (message) => {
    const response = await api.post("/api/chat/ai/", { message });
    return response.data;
  },

  geminiSymptomAnalysis: async (text) => {
    const response = await api.post("/api/chat/ai_symptoms/", { text });
    return response.data;
  },
};
