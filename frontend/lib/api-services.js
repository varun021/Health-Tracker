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

  getPredictionHistory: async (page = 1, pageSize = 20) => {
    const response = await api.get(`/api/predictions/history/?page=${page}&page_size=${pageSize}`);
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

  /** Train or retrain Naive Bayes model */
  trainModel: async () => {
    const response = await api.post('/api/predictions/train_model/');
    return response.data;
  },

  /** Import dataset (Testing.csv + severity/description/precaution) and auto-train */
  importDataset: async () => {
    const response = await api.post('/api/predictions/import_dataset/');
    return response.data;
  },

  /** Fetch model metadata (trained samples, total diseases, total symptoms) */
  getModelSummary: async () => {
    const response = await api.post('/api/predictions/train_model/');
    // We reuse train_model endpoint in "dry" mode — no re-training logic on backend
    // Alternatively, create a /model_summary/ endpoint later
    return response.data.details;
  },
};
