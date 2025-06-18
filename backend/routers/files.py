from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List
from pydantic import UUID4
from models.schemas import FileResponse
from services.file_service import FileService
from dependencies import get_supabase

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: UUID4 = Form(...),
    supabase=Depends(get_supabase)
):
    """Upload a PDF file to a folder"""
    file_service = FileService(supabase)
    return await file_service.upload_file(file, folder_id)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(file_id: UUID4, supabase=Depends(get_supabase)):
    """Get a specific file by ID"""
    file_service = FileService(supabase)
    return file_service.get_file(file_id)


@router.delete("/{file_id}")
async def delete_file(file_id: UUID4, supabase=Depends(get_supabase)):
    """Delete a file"""
    file_service = FileService(supabase)
    return file_service.delete_file(file_id) 