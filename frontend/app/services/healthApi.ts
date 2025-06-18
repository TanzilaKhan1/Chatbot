import apiClient from './apiClient';

// Health API endpoints
export const healthCheck = async () => {
  const response = await apiClient.get(`/health`);
  return response.data;
};

export const checkConfig = async () => {
  const response = await apiClient.get(`/config/check`);
  return response.data;
}; 