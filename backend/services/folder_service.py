from typing import List, Optional
from fastapi import HTTPException
from pydantic import UUID4
from models.schemas import FolderCreate, FolderUpdate


class FolderService:
    """Service for folder management operations"""
    
    def __init__(self, supabase):
        self.supabase = supabase
    
    def create_folder(self, folder: FolderCreate) -> dict:
        """Create a new folder"""
        try:
            response = self.supabase.table("folders").insert({
                "name": folder.name,
                "description": folder.description,
                "parent_id": str(folder.parent_id) if folder.parent_id else None
            }).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise HTTPException(status_code=400, detail="Failed to create folder")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_folders(self, parent_id: Optional[UUID4] = None) -> List[dict]:
        """Get all folders or folders by parent_id"""
        try:
            query = self.supabase.table("folders").select("*")
            
            if parent_id:
                query = query.eq("parent_id", str(parent_id))
            else:
                query = query.is_("parent_id", "null")
            
            response = query.execute()
            return response.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_folder(self, folder_id: UUID4) -> dict:
        """Get a specific folder by ID"""
        try:
            response = self.supabase.table("folders").select("*").eq("id", str(folder_id)).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise HTTPException(status_code=404, detail="Folder not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_folder(self, folder_id: UUID4, folder: FolderUpdate) -> dict:
        """Update a folder"""
        try:
            update_data = {}
            if folder.name is not None:
                update_data["name"] = folder.name
            if folder.description is not None:
                update_data["description"] = folder.description
            if folder.parent_id is not None:
                update_data["parent_id"] = str(folder.parent_id)
            
            response = self.supabase.table("folders").update(update_data).eq("id", str(folder_id)).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise HTTPException(status_code=404, detail="Folder not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_folder(self, folder_id: UUID4) -> dict:
        """Delete a folder"""
        try:
            response = self.supabase.table("folders").delete().eq("id", str(folder_id)).execute()
            return {"message": "Folder deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 