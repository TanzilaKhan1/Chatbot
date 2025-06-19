from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import List
from pydantic import UUID4
from models.schemas import FileResponse
from services.file_service import FileService
from dependencies import get_supabase

router = APIRouter(prefix="/api/files", tags=["files"])


async def process_file_background(file_id: str, folder_id: str, storage_path: str, original_filename: str, supabase_client):
    """Background task to process uploaded file and create embeddings"""
    try:
        print(f"Starting background processing for file: {original_filename}")
        
        # Import here to avoid circular imports
        from document_processor import DocumentProcessor
        from vector_store import VectorStore
        
        # Initialize processor and vector store
        processor = DocumentProcessor(supabase_client)
        vector_store = VectorStore(supabase_client=supabase_client)
        
        # Process the PDF and create chunks
        chunks = await processor.process_pdf(
            storage_path=storage_path,
            file_id=file_id,
            folder_id=folder_id,
            original_filename=original_filename
        )
        
        if chunks:
            # Add documents to vector store
            await vector_store.add_documents(chunks, file_id)
            print(f"Successfully processed and indexed {len(chunks)} chunks for {original_filename}")
        else:
            print(f"No chunks created for file {original_filename}")
            
    except Exception as e:
        print(f"Error processing file {original_filename}: {str(e)}")
        # You might want to update a status field in the database here
        # to indicate processing failed


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: UUID4 = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    supabase=Depends(get_supabase)
):
    """Upload a PDF file to a folder and automatically process it"""
    try:
        file_service = FileService(supabase)
        
        # Upload the file first
        upload_result = await file_service.upload_file(file, folder_id)
        
        if upload_result and "file" in upload_result:
            file_record = upload_result["file"]
            
            # Add background task to process the file
            background_tasks.add_task(
                process_file_background,
                file_id=file_record["id"],
                folder_id=str(folder_id),
                storage_path=file_record["storage_path"],
                original_filename=file_record["original_filename"],
                supabase_client=supabase
            )
            
            # Update the response to indicate processing has started
            upload_result["processing_status"] = "started"
            upload_result["message"] = "File uploaded successfully and processing started in background"
            
        return upload_result
        
    except Exception as e:
        print(f"Upload and process error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/{file_id}/process")
async def process_file_manually(
    file_id: UUID4,
    background_tasks: BackgroundTasks,
    supabase=Depends(get_supabase)
):
    """Manually trigger processing of an uploaded file"""
    try:
        # Get file information
        file_response = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = file_response.data[0]
        
        # Get folder information
        folder_response = supabase.table("folder_files").select("folder_id").eq("file_id", str(file_id)).execute()
        
        if not folder_response.data:
            raise HTTPException(status_code=404, detail="File not associated with any folder")
        
        folder_id = folder_response.data[0]["folder_id"]
        
        # Add background task
        background_tasks.add_task(
            process_file_background,
            file_id=str(file_id),
            folder_id=folder_id,
            storage_path=file_info["storage_path"],
            original_filename=file_info["original_filename"],
            supabase_client=supabase
        )
        
        return {
            "message": "File processing started in background", 
            "file_id": str(file_id),
            "filename": file_info["original_filename"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting file processing: {str(e)}")


@router.get("/{file_id}/processing-status")
async def get_file_processing_status(
    file_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Check if a file has been processed and indexed"""
    try:
        # Check if vectors exist for this file
        vector_response = supabase.table("document_vectors").select(
            "id", count="exact"
        ).eq("file_id", str(file_id)).execute()
        
        vector_count = vector_response.count if vector_response.count else 0
        
        # Get file info
        file_response = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = file_response.data[0]
        
        return {
            "file_id": str(file_id),
            "filename": file_info["original_filename"],
            "is_processed": vector_count > 0,
            "vector_count": vector_count,
            "status": "processed" if vector_count > 0 else "pending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking processing status: {str(e)}")


@router.post("/batch-process")
async def batch_process_files(
    folder_id: UUID4,
    background_tasks: BackgroundTasks,
    supabase=Depends(get_supabase)
):
    """Process all files in a folder that haven't been processed yet"""
    try:
        # Get all files in folder
        folder_files_response = supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", str(folder_id)).execute()
        
        if not folder_files_response.data:
            return {"message": "No files found in folder", "processed": 0}
        
        files_to_process = []
        
        for item in folder_files_response.data:
            file_data = item["files"]
            if file_data:
                # Check if file is already processed
                vector_response = supabase.table("document_vectors").select(
                    "id", count="exact"
                ).eq("file_id", file_data["id"]).execute()
                
                vector_count = vector_response.count if vector_response.count else 0
                
                if vector_count == 0:  # Not processed yet
                    files_to_process.append(file_data)
                    
                    # Add background task
                    background_tasks.add_task(
                        process_file_background,
                        file_id=file_data["id"],
                        folder_id=str(folder_id),
                        storage_path=file_data["storage_path"],
                        original_filename=file_data["original_filename"],
                        supabase_client=supabase
                    )
        
        return {
            "message": f"Started processing {len(files_to_process)} unprocessed files",
            "folder_id": str(folder_id),
            "files_to_process": len(files_to_process),
            "files": [{"id": f["id"], "name": f["original_filename"]} for f in files_to_process]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(file_id: UUID4, supabase=Depends(get_supabase)):
    """Get a specific file by ID"""
    file_service = FileService(supabase)
    return file_service.get_file(file_id)


@router.delete("/{file_id}")
async def delete_file(file_id: UUID4, supabase=Depends(get_supabase)):
    """Delete a file and its associated vectors"""
    try:
        file_service = FileService(supabase)
        
        # Delete vectors first
        try:
            from vector_store import VectorStore
            vector_store = VectorStore(supabase_client=supabase)
            await vector_store.delete_by_file_id(str(file_id))
            print(f"Deleted vectors for file {file_id}")
        except Exception as e:
            print(f"Error deleting vectors for file {file_id}: {e}")
            # Continue with file deletion even if vector deletion fails
        
        # Delete the file
        result = file_service.delete_file(file_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.get("/folder/{folder_id}/status")
async def get_folder_processing_status(
    folder_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Get processing status for all files in a folder"""
    try:
        # Get all files in folder
        folder_files_response = supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", str(folder_id)).execute()
        
        if not folder_files_response.data:
            return {
                "folder_id": str(folder_id),
                "total_files": 0,
                "processed_files": 0,
                "pending_files": 0,
                "files": []
            }
        
        file_statuses = []
        processed_count = 0
        
        for item in folder_files_response.data:
            file_data = item["files"]
            if file_data:
                # Check vector count for this file
                vector_response = supabase.table("document_vectors").select(
                    "id", count="exact"
                ).eq("file_id", file_data["id"]).execute()
                
                vector_count = vector_response.count if vector_response.count else 0
                is_processed = vector_count > 0
                
                if is_processed:
                    processed_count += 1
                
                file_statuses.append({
                    "file_id": file_data["id"],
                    "filename": file_data["original_filename"],
                    "is_processed": is_processed,
                    "vector_count": vector_count,
                    "file_size": file_data["file_size"]
                })
        
        total_files = len(file_statuses)
        pending_files = total_files - processed_count
        
        return {
            "folder_id": str(folder_id),
            "total_files": total_files,
            "processed_files": processed_count,
            "pending_files": pending_files,
            "processing_complete": pending_files == 0,
            "files": file_statuses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting folder status: {str(e)}")