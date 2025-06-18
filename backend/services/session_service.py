from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from models.schemas import SessionCreate, MessageCreate, SessionResponse, MessageResponse, SessionWithMessages


class SessionService:
    """Service for managing chat sessions and messages"""
    
    def __init__(self, supabase):
        self.supabase = supabase
    
    def create_session(self, session_data: SessionCreate) -> SessionResponse:
        """Create a new chat session"""
        try:
            data = {
                "folder_id": str(session_data.folder_id),
                "title": session_data.title,
                "model": session_data.model
            }
            
            response = self.supabase.table("sessions").insert(data).execute()
            
            if response.data:
                return SessionResponse(**response.data[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to create session")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")
    
    def get_session(self, session_id: UUID) -> SessionWithMessages:
        """Get a session with all its messages"""
        try:
            # Get session
            session_response = self.supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
            
            if not session_response.data:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = session_response.data[0]
            
            # Get messages for this session
            messages_response = self.supabase.table("messages").select("*").eq(
                "session_id", str(session_id)
            ).order("created_at").execute()
            
            messages = messages_response.data if messages_response.data else []
            
            return SessionWithMessages(
                **session,
                messages=[MessageResponse(**msg) for msg in messages]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_folder_sessions(self, folder_id: UUID) -> List[SessionResponse]:
        """Get all sessions for a folder"""
        try:
            response = self.supabase.table("sessions").select("*").eq(
                "folder_id", str(folder_id)
            ).order("created_at", desc=True).execute()
            
            return [SessionResponse(**session) for session in response.data]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def add_message(self, message_data: MessageCreate) -> MessageResponse:
        """Add a message to a session"""
        try:
            data = {
                "session_id": str(message_data.session_id),
                "role": message_data.role,
                "content": message_data.content
            }
            
            response = self.supabase.table("messages").insert(data).execute()
            
            if response.data:
                # Update session's updated_at timestamp
                self.supabase.table("sessions").update({
                    "updated_at": "now()"
                }).eq("id", str(message_data.session_id)).execute()
                
                return MessageResponse(**response.data[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to add message")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Message creation failed: {str(e)}")
    
    def update_session_title(self, session_id: UUID, title: str) -> SessionResponse:
        """Update session title"""
        try:
            response = self.supabase.table("sessions").update({
                "title": title
            }).eq("id", str(session_id)).execute()
            
            if response.data:
                return SessionResponse(**response.data[0])
            else:
                raise HTTPException(status_code=404, detail="Session not found")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_session(self, session_id: UUID) -> dict:
        """Delete a session (messages will be cascade deleted)"""
        try:
            response = self.supabase.table("sessions").delete().eq("id", str(session_id)).execute()
            
            if response.data:
                return {"message": "Session deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Session not found")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        