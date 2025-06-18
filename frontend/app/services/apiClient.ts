// app/services/apiClient.ts
import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL
});

// Add request/response interceptors for debugging
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    if (config.data instanceof FormData) {
      console.log('FormData keys:', Array.from(config.data.keys()));
    }
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export default apiClient; 