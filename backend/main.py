# main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
import os
from supabase import create_client, Client
import asyncio
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Folder File Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = "pdf-files"  # Create this bucket in Supabase Storage

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic models
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

# Folder endpoints
@app.post("/api/folders", response_model=FolderResponse)
async def create_folder(folder: FolderCreate):
    """Create a new folder"""
    try:
        response = supabase.table("folders").insert({
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

@app.get("/api/folders", response_model=List[FolderResponse])
async def get_folders(parent_id: Optional[UUID4] = None):
    """Get all folders or folders by parent_id"""
    try:
        query = supabase.table("folders").select("*")
        
        if parent_id:
            query = query.eq("parent_id", str(parent_id))
        else:
            query = query.is_("parent_id", "null")
        
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(folder_id: UUID4):
    """Get a specific folder by ID"""
    try:
        response = supabase.table("folders").select("*").eq("id", str(folder_id)).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="Folder not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(folder_id: UUID4, folder: FolderUpdate):
    """Update a folder"""
    try:
        update_data = {}
        if folder.name is not None:
            update_data["name"] = folder.name
        if folder.description is not None:
            update_data["description"] = folder.description
        if folder.parent_id is not None:
            update_data["parent_id"] = str(folder.parent_id)
        
        response = supabase.table("folders").update(update_data).eq("id", str(folder_id)).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="Folder not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: UUID4):
    """Delete a folder"""
    try:
        response = supabase.table("folders").delete().eq("id", str(folder_id)).execute()
        return {"message": "Folder deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File endpoints
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: UUID4 = Form(...)
):
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
            supabase.storage.create_bucket(SUPABASE_BUCKET, {"public": True})
        except:
            pass  # Bucket already exists
        
        # Upload to Supabase Storage
        try:
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).upload(
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
            storage_response = supabase.storage.from_(SUPABASE_BUCKET).upload(
                storage_path,
                content,
                {"content-type": "application/pdf"}
            )
        
        # Get public URL
        file_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
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
        file_response = supabase.table("files").insert(file_data).execute()
        print(f"File insert response: {file_response}")
        
        if file_response.data and len(file_response.data) > 0:
            file_record = file_response.data[0]
            
            # Create folder-file relationship
            relation_data = {
                "folder_id": str(folder_id),
                "file_id": file_record["id"]
            }
            print(f"Creating folder-file relation: {relation_data}")
            relation_response = supabase.table("folder_files").insert(relation_data).execute()
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

@app.get("/api/folders/{folder_id}/files", response_model=List[FileResponse])
async def get_folder_files(folder_id: UUID4):
    """Get all files in a folder"""
    try:
        # Query files through the relationship table
        response = supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", str(folder_id)).execute()
        
        # Extract files from the response
        files = [item["files"] for item in response.data if item["files"]]
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}", response_model=FileResponse)
async def get_file(file_id: UUID4):
    """Get a specific file by ID"""
    try:
        response = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: UUID4):
    """Delete a file"""
    try:
        # Get file info first
        file_response = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = file_response.data[0]
        
        # Delete from storage
        supabase.storage.from_(SUPABASE_BUCKET).remove([file_info["storage_path"]])
        
        # Delete from database (cascade will handle folder_files)
        supabase.table("files").delete().eq("id", str(file_id)).execute()
        
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Folder File Management API"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify Supabase connection"""
    try:
        # Check database connection
        folders_response = supabase.table("folders").select("id").limit(1).execute()
        
        # Check if bucket exists
        try:
            buckets = supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == SUPABASE_BUCKET for bucket in buckets)
        except:
            bucket_exists = False
        
        return {
            "status": "healthy",
            "database": "connected",
            "storage_bucket": SUPABASE_BUCKET,
            "bucket_exists": bucket_exists,
            "supabase_url": SUPABASE_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "supabase_url": SUPABASE_URL
        }

