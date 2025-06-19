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

export const geminiChatWithDocuments = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>(`/chat/gemini`, request, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error: any) {
    console.error('Gemini chat failed:', error);
    if (error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Gemini chat failed');
    }
    throw error;
  }
};

export const ollamaChatWithDocuments = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>(`/chat/ollama`, request, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error: any) {
    console.error('Ollama chat failed:', error);
    if (error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Ollama chat failed');
    }
    throw error;
  }
};

export const smartChatWithDocuments = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>(`/chat/smart`, request, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error: any) {
    console.error('Smart chat failed:', error);
    if (error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Smart chat failed');
    }
    throw error;
  }
};

export const getModelsStatus = async () => {
  try {
    const response = await apiClient.get(`/chat/models/status`);
    return response.data;
  } catch (error: any) {
    console.error('Failed to get models status:', error);
    throw error;
  }
};

export const chatWithSession = async (
  message: string,
  folderId: string,
  sessionId?: string,
  model: string = 'Smart'
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
    
    // Check if error is API quota exceeded
    const isQuotaError = 
      error.response?.data?.detail?.includes('insufficient_quota') || 
      error.response?.data?.detail?.includes('quota') ||
      error.response?.data?.detail?.includes('rate limit');
    
    if (isQuotaError && (model === 'OpenAI' || model === 'Gemini' || model === 'Ollama')) {
      console.log(`${model} quota/rate limit exceeded, falling back to Smart mode...`);
      // Try again with Smart mode (will automatically select best available)
      const fallbackParams = new URLSearchParams({
        message,
        folder_id: folderId,
        model: 'Smart'
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

// Check if all files in a folder are indexed and ready for querying
export const checkFolderFilesIndexed = async (folderId: string): Promise<{ indexed: boolean, storage?: string }> => {
  try {
    const response = await apiClient.get(`/chat/folder/${folderId}/indexed`);
    return {
      indexed: (response.data as { indexed: boolean, storage?: string }).indexed,
      storage: (response.data as { indexed: boolean, storage?: string }).storage
    };
  } catch (error) {
    console.error('Error checking if folder files are indexed:', error);
    // If there's an error, we'll assume files are ready to avoid false negatives
    return { indexed: true };
  }
}; 