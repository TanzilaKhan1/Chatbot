// app/services/api.ts
import axios from 'axios';
import { ApiFolder, FileItem } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

// Add request/response interceptors for debugging
axios.interceptors.request.use(
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

axios.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Folders API
export const fetchFolders = async () => {
  const response = await axios.get<ApiFolder[]>(`${API_BASE_URL}/folders`);
  return response.data;
};

export const createFolder = async (name: string) => {
  const response = await axios.post(`${API_BASE_URL}/folders`, { name });
  return response.data;
};

export const deleteFolder = async (folderId: string) => {
  const response = await axios.delete(`${API_BASE_URL}/folders/${folderId}`);
  return response.data;
};

// Files API
export const fetchFolderFiles = async (folderId: string) => {
  const response = await axios.get<FileItem[]>(`${API_BASE_URL}/folders/${folderId}/files`);
  return response.data;
};

export const uploadFile = async (file: File, folderId: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('folder_id', folderId);

  console.log('Uploading file:', file.name, 'to folder:', folderId);
  console.log('File type:', file.type);
  console.log('File size:', file.size);

  try {
    const response = await axios.post(`${API_BASE_URL}/files/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    console.log('Upload successful:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Upload failed:', error);
    if (error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Upload failed');
    }
    throw error;
  }
};

export const deleteFile = async (fileId: string) => {
  const response = await axios.delete(`${API_BASE_URL}/files/${fileId}`);
  return response.data;
};