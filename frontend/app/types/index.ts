// app/types/index.ts
export interface ApiFolder {
  id: string;
  name: string;
  description?: string;
  parent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface FolderWithFiles extends ApiFolder {
  fileCount: number;
}

export interface FileItem {
  id: string;
  filename: string;
  original_filename: string;
  file_size?: number;
  mime_type?: string;
  file_url: string;
  storage_path: string;
  created_at: string;
  updated_at: string;
}