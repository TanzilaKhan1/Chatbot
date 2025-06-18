from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import UUID4
from models.schemas import FolderCreate, FolderUpdate, FolderResponse
from services.folder_service import FolderService
from dependencies import get_supabase

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.post("", response_model=FolderResponse)
async def create_folder(folder: FolderCreate, supabase=Depends(get_supabase)):
    """Create a new folder"""
    folder_service = FolderService(supabase)
    return folder_service.create_folder(folder)


@router.get("", response_model=List[FolderResponse])
async def get_folders(parent_id: Optional[UUID4] = None, supabase=Depends(get_supabase)):
    """Get all folders or folders by parent_id"""
    folder_service = FolderService(supabase)
    return folder_service.get_folders(parent_id)


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(folder_id: UUID4, supabase=Depends(get_supabase)):
    """Get a specific folder by ID"""
    folder_service = FolderService(supabase)
    return folder_service.get_folder(folder_id)


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(folder_id: UUID4, folder: FolderUpdate, supabase=Depends(get_supabase)):
    """Update a folder"""
    folder_service = FolderService(supabase)
    return folder_service.update_folder(folder_id, folder)


@router.delete("/{folder_id}")
async def delete_folder(folder_id: UUID4, supabase=Depends(get_supabase)):
    """Delete a folder"""
    folder_service = FolderService(supabase)
    return folder_service.delete_folder(folder_id) 