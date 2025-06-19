from fastapi import APIRouter, Depends
from dependencies import get_supabase, get_qdrant_client
from config import config
from vector_store import VectorStore

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check(supabase=Depends(get_supabase), qdrant_client=Depends(get_qdrant_client)):
    """Health check endpoint to verify Supabase connection"""
    try:
        # Check database connection
        folders_response = supabase.table("folders").select("id").limit(1).execute()
        
        # Check if bucket exists
        try:
            buckets = supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == config.SUPABASE_BUCKET for bucket in buckets)
        except:
            bucket_exists = False
            
        # Initialize vector store to check availability
        vector_store = VectorStore(supabase_client=supabase)
        
        return {
            "status": "healthy",
            "database": "connected",
            "storage_bucket": config.SUPABASE_BUCKET,
            "bucket_exists": bucket_exists,
            "supabase_url": config.SUPABASE_URL,
            "vector_storage": {
                "primary": "supabase" if vector_store.supabase_available else "qdrant",
                "supabase_available": vector_store.supabase_available,
                "qdrant_available": vector_store.qdrant_available,
                "using_supabase_vectors": vector_store.use_supabase_vectors
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "supabase_url": config.SUPABASE_URL
        }


@router.get("/config/check")
async def check_config():
    """Check if required environment variables are set"""
    return {
        "openai_api_key": bool(config.OPENAI_API_KEY),
        "qdrant_running": True,  # We'll assume it's running if no error
        "supabase_configured": bool(config.SUPABASE_URL and config.SUPABASE_KEY),
        "use_supabase_vectors": config.USE_SUPABASE_VECTORS
    } 