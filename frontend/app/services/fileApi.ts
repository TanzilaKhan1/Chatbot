// app/services/fileApi.ts
import apiClient from './apiClient';
import { FileItem } from '../types';

// Files API endpoints
export const fetchFolderFiles = async (folderId: string) => {
  // Note: This endpoint is actually in the chat router, not files router
  const response = await apiClient.get<FileItem[]>(`/folders/${folderId}/files`);
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
    const response = await apiClient.post(`/files/upload`, formData, {
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

export const getFile = async (fileId: string) => {
  const response = await apiClient.get(`/files/${fileId}`);
  return response.data;
};

export const deleteFile = async (fileId: string) => {
  const response = await apiClient.delete(`/files/${fileId}`);
  return response.data;
}; 