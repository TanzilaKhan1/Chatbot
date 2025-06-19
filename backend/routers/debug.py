# Debug routes for troubleshooting
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import UUID4
from models.schemas import ChatRequest, ChatResponse, FileResponse, SessionCreate, MessageCreate
from services.chat_service import ChatService
from services.file_service import FileService
from services.session_service import SessionService
from dependencies import get_supabase, get_embeddings, get_llm, get_qdrant_client, get_gemini_model, get_chat_service
from vector_store import VectorStore
from document_processor import DocumentProcessor
        
        
router = APIRouter(prefix="/api/debug", tags=["debug"])


async def process_file_background(file_id: str, folder_id: str, storage_path: str, original_filename: str, supabase_client):
    """Background task to process uploaded file and create embeddings"""
    try:
        print(f"Starting background processing for file: {original_filename}")
        
        
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


@router.get("/folder/{folder_id}/files")
async def debug_folder_files(
    folder_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Debug: Get detailed information about files in a folder"""
    try:
        # Get files from folder_files table
        folder_files_response = supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", str(folder_id)).execute()
        
        files_info = []
        if folder_files_response.data:
            for item in folder_files_response.data:
                file_data = item["files"]
                if file_data:
                    files_info.append(file_data)
        
        # Check vector embeddings for each file
        vector_info = []
        for file_info in files_info:
            # Check Supabase vectors
            supabase_count = supabase.table("document_vectors").select(
                "id", count="exact"
            ).eq("file_id", file_info["id"]).execute()
            
            vector_info.append({
                "file_id": file_info["id"],
                "filename": file_info["original_filename"],
                "supabase_vectors": supabase_count.count if supabase_count.count else 0,
                "file_size": file_info["file_size"],
                "storage_path": file_info["storage_path"]
            })
        
        return {
            "folder_id": str(folder_id),
            "files": files_info,
            "vector_summary": vector_info,
            "total_files": len(files_info)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")


@router.post("/process-all-files/{folder_id}")
async def debug_process_all_files(
    folder_id: UUID4,
    background_tasks: BackgroundTasks,
    supabase=Depends(get_supabase)
):
    """Debug: Force process all files in a folder"""
    try:
        # Get all files in folder
        folder_files_response = supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", str(folder_id)).execute()
        
        if not folder_files_response.data:
            return {"message": "No files found in folder", "processed": 0}
        
        files_processed = 0
        for item in folder_files_response.data:
            file_data = item["files"]
            if file_data:
                background_tasks.add_task(
                    process_file_background,
                    file_id=file_data["id"],
                    folder_id=str(folder_id),
                    storage_path=file_data["storage_path"],
                    original_filename=file_data["original_filename"],
                    supabase_client=supabase
                )
                files_processed += 1
        
        return {
            "message": f"Started processing {files_processed} files",
            "folder_id": str(folder_id),
            "files_processed": files_processed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug processing error: {str(e)}")


@router.get("/vector-store/status")
async def debug_vector_store_status(
    supabase=Depends(get_supabase)
):
    """Debug: Check vector store status and statistics"""
    try:
        vector_store = VectorStore(supabase_client=supabase)
        
        # Check Supabase vectors
        supabase_total = None
        supabase_error = None
        try:
            response = supabase.table("document_vectors").select("id", count="exact").execute()
            supabase_total = response.count if response.count else 0
        except Exception as e:
            supabase_error = str(e)
        
        # Check Qdrant vectors (if available)
        qdrant_info = None
        qdrant_error = None
        try:
            if vector_store.qdrant_available:
                collections = vector_store.qdrant_client.get_collections()
                qdrant_info = {
                    "available": True,
                    "collections": [col.name for col in collections.collections]
                }
        except Exception as e:
            qdrant_error = str(e)
        
        return {
            "supabase_vectors": {
                "available": vector_store.supabase_available,
                "total_documents": supabase_total,
                "error": supabase_error
            },
            "qdrant_vectors": {
                "available": vector_store.qdrant_available,
                "info": qdrant_info,
                "error": qdrant_error
            },
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dimension": 384
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector store status error: {str(e)}")


@router.delete("/folder/{folder_id}/vectors")
async def debug_delete_folder_vectors(
    folder_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Debug: Delete all vectors for a folder"""
    try:
        vector_store = VectorStore(supabase_client=supabase)
        
        # Delete from Supabase
        supabase_deleted = 0
        try:
            response = supabase.table("document_vectors").delete().eq("folder_id", str(folder_id)).execute()
            supabase_deleted = len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error deleting from Supabase: {e}")
        
        # Delete from Qdrant (if available)
        qdrant_deleted = 0
        try:
            if vector_store.qdrant_available:
                # This would require implementing folder-based deletion in Qdrant
                pass
        except Exception as e:
            print(f"Error deleting from Qdrant: {e}")
        
        return {
            "message": "Vectors deleted",
            "folder_id": str(folder_id),
            "supabase_deleted": supabase_deleted,
            "qdrant_deleted": qdrant_deleted
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector deletion error: {str(e)}")


@router.get("/file/{file_id}/vectors")
async def debug_file_vectors(
    file_id: UUID4,
    supabase=Depends(get_supabase)
):
    """Debug: Get vector information for a specific file"""
    try:
        # Get file info
        file_response = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = file_response.data[0]
        
        # Get vectors for this file
        vectors_response = supabase.table("document_vectors").select(
            "id", "chunk_index", "page_number", "content"
        ).eq("file_id", str(file_id)).execute()
        
        vectors = vectors_response.data if vectors_response.data else []
        
        # Get sample content from first few chunks
        sample_chunks = []
        for vector in vectors[:3]:  # First 3 chunks
            sample_chunks.append({
                "chunk_index": vector["chunk_index"],
                "page_number": vector.get("page_number"),
                "content_preview": vector["content"][:200] + "..." if len(vector["content"]) > 200 else vector["content"]
            })
        
        return {
            "file_id": str(file_id),
            "filename": file_info["original_filename"],
            "file_size": file_info["file_size"],
            "total_vectors": len(vectors),
            "sample_chunks": sample_chunks,
            "all_chunk_indices": [v["chunk_index"] for v in vectors]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file vectors: {str(e)}")


@router.post("/test-embedding")
async def debug_test_embedding(
    text: str = "This is a test query",
    supabase=Depends(get_supabase)
):
    """Debug: Test embedding generation"""
    try:
        vector_store = VectorStore(supabase_client=supabase)
        
        # Generate embedding
        embedding = vector_store.embeddings.embed_query(text)
        
        return {
            "text": text,
            "embedding_dimension": len(embedding),
            "embedding_sample": embedding[:5],  # First 5 values
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding test error: {str(e)}")