// app/types/api.ts
import { ApiFolder, FileItem } from './index';

// Chat interfaces
export interface ChatRequest {
  message: string;
  folder_id: string;
}

export interface ChatResponse {
  response: string;
  sources: string[];
}

// Session interfaces
export interface SessionCreate {
  folder_id: string;
  title: string;
  model: string;
}

export interface SessionResponse {
  id: string;
  folder_id: string;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
}

export interface MessageCreate {
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
}

export interface MessageResponse {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface SessionWithMessages extends SessionResponse {
  messages: MessageResponse[];
}

export interface ChatWithSessionResponse {
  session_id: string;
  response: string;
  sources: string[];
  model?: string;
} 