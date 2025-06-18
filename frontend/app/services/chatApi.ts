// app/services/chatApi.ts
import apiClient from './apiClient';
import { ChatRequest, ChatResponse, ChatWithSessionResponse } from '../types/api';

// Chat API endpoints
export const chatWithDocuments = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>(`/chat`, request, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error: any) {
    console.error('Chat failed:', error);
    if (error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Chat failed');
    }
    throw error;
  }
};

export const simpleChatWithDocuments = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>(`/chat/simple`, request, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error: any) {
    console.error('Simple chat failed:', error);
    if (error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Simple chat failed');
    }
    throw error;
  }
};

export const checkSimpleChatHealth = async () => {
  const response = await apiClient.get(`/chat/simple/health`);
  return response.data;
};

export const chatWithSession = async (
  message: string,
  folderId: string,
  sessionId?: string,
  model: string = 'OpenAI'
): Promise<ChatWithSessionResponse> => {
  const params = new URLSearchParams({
    message,
    folder_id: folderId,
    model
  });
  
  if (sessionId) {
    params.append('session_id', sessionId);
  }
  
  try {
    const response = await apiClient.post<ChatWithSessionResponse>(
      `/chat/with-session?${params.toString()}`
    );
    return response.data;
  } catch (error: any) {
    console.error('Chat with session failed:', error);
    
    // Check if error is OpenAI quota exceeded (insufficient_quota)
    const isQuotaError = 
      error.response?.data?.detail?.includes('insufficient_quota') || 
      error.response?.data?.detail?.includes('quota');
    
    if (isQuotaError && model === 'OpenAI') {
      console.log('OpenAI quota exceeded, falling back to simple chat...');
      // Try again with simple chat
      const fallbackParams = new URLSearchParams({
        message,
        folder_id: folderId,
        model: 'Simple'  // Switch to simple chat
      });
      
      if (sessionId) {
        fallbackParams.append('session_id', sessionId);
      }
      
      const fallbackResponse = await apiClient.post<ChatWithSessionResponse>(
        `/chat/with-session?${fallbackParams.toString()}`
      );
      return fallbackResponse.data;
    }
    
    throw error;
  }
}; 