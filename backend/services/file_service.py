import os
from datetime import datetime
from uuid import uuid4
from typing import List
from fastapi import UploadFile, HTTPException
from pydantic import UUID4
from config import config


class FileService:
    """Service for file management operations"""
    
    def __init__(self, supabase):
        self.supabase = supabase
    
    async def upload_file(self, file: UploadFile, folder_id: UUID4) -> dict:
        """Upload a PDF file to a folder"""
        try:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            
            # Generate unique filename
            file_id = str(uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            storage_filename = f"{file_id}{file_extension}"
            storage_path = f"pdfs/{storage_filename}"
            
            # Read file content
            content = await file.read()
            
            print(f"Uploading file: {file.filename} ({len(content)} bytes)")
            
            # First, check if bucket exists and create if needed
            try:
                # Try to create the bucket (will fail if it already exists, which is fine)
                self.supabase.storage.create_bucket(config.SUPABASE_BUCKET, {"public": True})
            except:
                pass  # Bucket already exists
            
            # Upload to Supabase Storage
            try:
                storage_response = self.supabase.storage.from_(config.SUPABASE_BUCKET).upload(
                    storage_path,
                    content,
                    {"content-type": "application/pdf"}
                )
                print(f"Storage response: {storage_response}")
            except Exception as storage_error:
                print(f"Storage error: {storage_error}")
                # If file already exists, try with a different name
                storage_filename = f"{file_id}_{int(datetime.now().timestamp())}{file_extension}"
                storage_path = f"pdfs/{storage_filename}"
                storage_response = self.supabase.storage.from_(config.SUPABASE_BUCKET).upload(
                    storage_path,
                    content,
                    {"content-type": "application/pdf"}
                )
            
            # Get public URL
            file_url = self.supabase.storage.from_(config.SUPABASE_BUCKET).get_public_url(storage_path)
            print(f"File URL: {file_url}")
            
            # Save file metadata to database
            file_data = {
                "filename": storage_filename,
                "original_filename": file.filename,
                "file_size": len(content),
                "mime_type": "application/pdf",
                "file_url": file_url,
                "storage_path": storage_path
            }
            
            print(f"Inserting file data: {file_data}")
            file_response = self.supabase.table("files").insert(file_data).execute()
            print(f"File insert response: {file_response}")
            
            if file_response.data and len(file_response.data) > 0:
                file_record = file_response.data[0]
                
                # Create folder-file relationship
                relation_data = {
                    "folder_id": str(folder_id),
                    "file_id": file_record["id"]
                }
                print(f"Creating folder-file relation: {relation_data}")
                relation_response = self.supabase.table("folder_files").insert(relation_data).execute()
                print(f"Relation response: {relation_response}")
                
                return {
                    "message": "File uploaded successfully",
                    "file": file_record
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to save file metadata")
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"Upload error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    def get_folder_files(self, folder_id: UUID4) -> List[dict]:
        """Get all files in a folder"""
        try:
            # Query files through the relationship table
            response = self.supabase.table("folder_files").select(
                "files(*)"
            ).eq("folder_id", str(folder_id)).execute()
            
            # Extract files from the response
            files = [item["files"] for item in response.data if item["files"]]
            return files
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_file(self, file_id: UUID4) -> dict:
        """Get a specific file by ID"""
        try:
            response = self.supabase.table("files").select("*").eq("id", str(file_id)).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_file(self, file_id: UUID4) -> dict:
        """Delete a file"""
        try:
            # Get file info first
            file_response = self.supabase.table("files").select("*").eq("id", str(file_id)).execute()
            
            if not file_response.data:
                raise HTTPException(status_code=404, detail="File not found")
            
            file_info = file_response.data[0]
            
            # Delete from storage
            self.supabase.storage.from_(config.SUPABASE_BUCKET).remove([file_info["storage_path"]])
            
            # Delete from database (cascade will handle folder_files)
            self.supabase.table("files").delete().eq("id", str(file_id)).execute()
            
            return {"message": "File deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 