// app/services/sessionApi.ts
import apiClient from './apiClient';
import { 
  SessionCreate, 
  SessionResponse, 
  MessageCreate, 
  MessageResponse,
  SessionWithMessages 
} from '../types/api';

// Sessions API endpoints
export const createSession = async (sessionData: SessionCreate): Promise<SessionResponse> => {
  const response = await apiClient.post<SessionResponse>(`/sessions`, sessionData);
  return response.data;
};

export const getSession = async (sessionId: string): Promise<SessionWithMessages> => {
  const response = await apiClient.get<SessionWithMessages>(`/sessions/${sessionId}`);
  return response.data;
};

export const getFolderSessions = async (folderId: string): Promise<SessionResponse[]> => {
  const response = await apiClient.get<SessionResponse[]>(`/sessions/folder/${folderId}`);
  return response.data;
};

export const addMessage = async (messageData: MessageCreate): Promise<MessageResponse> => {
  const response = await apiClient.post<MessageResponse>(`/sessions/messages`, messageData);
  return response.data;
};

export const updateSessionTitle = async (sessionId: string, title: string): Promise<SessionResponse> => {
  const response = await apiClient.put<SessionResponse>(`/sessions/${sessionId}/title?title=${encodeURIComponent(title)}`);
  return response.data;
};

export const deleteSession = async (sessionId: string): Promise<void> => {
  await apiClient.delete(`/sessions/${sessionId}`);
}; 