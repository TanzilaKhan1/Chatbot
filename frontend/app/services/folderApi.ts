import apiClient from './apiClient';
import { ApiFolder } from '../types';

// Folders API endpoints
export const fetchFolders = async (parent_id?: string) => {
  const params = parent_id ? { parent_id } : {};
  const response = await apiClient.get<ApiFolder[]>(`/folders`, { params });
  return response.data;
};

export const createFolder = async (name: string, description?: string, parent_id?: string) => {
  const response = await apiClient.post(`/folders`, { 
    name, 
    description,
    parent_id 
  });
  return response.data;
};

export const getFolder = async (folderId: string) => {
  const response = await apiClient.get(`/folders/${folderId}`);
  return response.data;
};

export const updateFolder = async (folderId: string, updates: { name?: string; description?: string; parent_id?: string }) => {
  const response = await apiClient.put(`/folders/${folderId}`, updates);
  return response.data;
};

export const deleteFolder = async (folderId: string) => {
  const response = await apiClient.delete(`/folders/${folderId}`);
  return response.data;
}; 