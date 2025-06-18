from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import UUID4
from models.schemas import (
    SessionCreate, SessionResponse, MessageCreate, 
    MessageResponse, SessionWithMessages
)
from services.session_service import SessionService
from dependencies import get_supabase

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    supabase=Depends(get_supabase)
):
    """Create a new chat session"""
    session_service = SessionService(supabase)
    return session_service.create_session(session_data)


@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Get a session with all its messages"""
    session_service = SessionService(supabase)
    return session_service.get_session(session_id)


@router.get("/folder/{folder_id}", response_model=List[SessionResponse])
async def get_folder_sessions(
    folder_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Get all sessions for a specific folder"""
    session_service = SessionService(supabase)
    return session_service.get_folder_sessions(folder_id)


@router.post("/messages", response_model=MessageResponse)
async def add_message(
    message_data: MessageCreate,
    supabase=Depends(get_supabase)
):
    """Add a message to a session"""
    session_service = SessionService(supabase)
    return session_service.add_message(message_data)


@router.put("/{session_id}/title")
async def update_session_title(
    session_id: UUID4,
    title: str,
    supabase=Depends(get_supabase)
):
    """Update session title"""
    session_service = SessionService(supabase)
    return session_service.update_session_title(session_id, title)


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Delete a session"""
    session_service = SessionService(supabase)
    return session_service.delete_session(session_id)