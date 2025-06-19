from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime


class FolderCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID4] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID4] = None


class FolderResponse(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    parent_id: Optional[UUID4]
    created_at: datetime
    updated_at: datetime


class FileResponse(BaseModel):
    id: UUID4
    filename: str
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    file_url: str
    storage_path: str
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    message: str
    folder_id: UUID4


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = [] 
    

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []


class SessionCreate(BaseModel):
    folder_id: UUID4
    title: str
    model: str = "OpenAI"


class SessionResponse(BaseModel):
    id: UUID4
    folder_id: UUID4
    title: str
    model: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    session_id: UUID4
    role: str
    content: str


class MessageResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    role: str
    content: str
    created_at: datetime


class SessionWithMessages(SessionResponse):
    messages: List[MessageResponse] = []
    
