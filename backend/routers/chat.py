from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import UUID4
from models.schemas import ChatRequest, ChatResponse, FileResponse, SessionCreate, MessageCreate
from services.chat_service import ChatService
from services.file_service import FileService
from services.session_service import SessionService
from dependencies import get_supabase, get_embeddings, get_llm, get_qdrant_client, get_gemini_model, get_chat_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/folders/{folder_id}/files", response_model=List[FileResponse])
async def get_folder_files(folder_id: UUID4, supabase=Depends(get_supabase)):
    """Get all files in a folder"""
    file_service = FileService(supabase)
    return file_service.get_folder_files(folder_id)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client)
):
    """Chat with documents in a folder using AI"""
    try:
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client)
        return await chat_service.chat_with_openai(request)
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/chat/gemini", response_model=ChatResponse)
async def gemini_chat_with_documents(
    request: ChatRequest,
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client),
    gemini_model=Depends(get_gemini_model)
):
    """Chat with documents using Google Gemini"""
    try:
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, gemini_model)
        return await chat_service.chat_with_gemini(request)
    except Exception as e:
        print(f"Gemini chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini chat failed: {str(e)}")


@router.post("/chat/ollama", response_model=ChatResponse)
async def ollama_chat_with_documents(
    request: ChatRequest,
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client),
    gemini_model=Depends(get_gemini_model)
):
    """Chat with documents using Ollama local LLM"""
    try:
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, gemini_model)
        return await chat_service.chat_with_ollama(request)
    except Exception as e:
        print(f"Ollama chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ollama chat failed: {str(e)}")


@router.post("/chat/smart", response_model=ChatResponse)
async def smart_chat_with_documents(
    request: ChatRequest,
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client),
    gemini_model=Depends(get_gemini_model)
):
    """Smart chat that automatically selects the best available model (OpenAI -> Gemini -> Ollama)"""
    try:
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, gemini_model)
        return await chat_service.smart_chat(request)
    except Exception as e:
        print(f"Smart chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Smart chat failed: {str(e)}")


@router.get("/chat/models/status")
async def get_models_status():
    """Check the status of all available chat models"""
    from dependencies import check_openai_api_key, check_gemini_api_key, check_ollama_availability
    from config import config
    
    openai_available = check_openai_api_key()
    gemini_available = check_gemini_api_key()
    ollama_available = check_ollama_availability()
    
    # Determine recommended model
    if openai_available:
        recommended = "openai"
    elif gemini_available:
        recommended = "gemini"
    elif ollama_available:
        recommended = "ollama"
    else:
        recommended = "unavailable"
    
    return {
        "models": {
            "openai": {
                "available": openai_available,
                "name": "OpenAI GPT",
                "description": "Advanced AI model with high accuracy"
            },
            "gemini": {
                "available": gemini_available,
                "name": "Google Gemini",
                "description": "Google's advanced AI model"
            },
            "ollama": {
                "available": ollama_available,
                "name": "Ollama Local LLM",
                "description": f"Local LLM running via Ollama (model: {config.OLLAMA_MODEL})"
            }
        },
        "recommended": recommended,
        "smart_mode_available": True
    }
        

@router.post("/chat/with-session", response_model=dict)
async def chat_with_session(
    message: str,
    folder_id: UUID4,
    session_id: Optional[UUID4] = None,
    model: str = "Smart",
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client),
    gemini_model=Depends(get_gemini_model)
):
    """Chat with documents and maintain session history"""
    try:
        session_service = SessionService(supabase)
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, gemini_model)
        
        # Create or get session
        if not session_id:
            # Create new session with message preview as title
            title = message[:50] + "..." if len(message) > 50 else message
            session = session_service.create_session(SessionCreate(
                folder_id=folder_id,
                title=title,
                model=model
            ))
            session_id = session.id
        
        # Add user message to session
        session_service.add_message(MessageCreate(
            session_id=session_id,
            role="user",
            content=message
        ))
        
        # Get chat response
        chat_request = ChatRequest(message=message, folder_id=folder_id)
        
        # Choose model based on preference
        if model == "Smart":
            # Use smart chat that automatically selects the best model
            chat_response = await chat_service.smart_chat(chat_request)
        elif model == "OpenAI":
            try:
                chat_response = await chat_service.chat_with_openai(chat_request)
            except Exception as openai_error:
                # Check if it's a quota error
                error_str = str(openai_error).lower()
                if 'quota' in error_str or 'insufficient_quota' in error_str or '429' in error_str:
                    print("OpenAI quota exceeded, falling back to smart chat")
                    # Fall back to smart chat (will try Gemini then Ollama)
                    chat_response = await chat_service.smart_chat(chat_request)
                    chat_response.response = f"[Note: Using fallback model due to OpenAI quota limits]\n\n{chat_response.response}"
                else:
                    # Re-raise if it's not a quota error
                    raise
        elif model == "Gemini":
            try:
                chat_response = await chat_service.chat_with_gemini(chat_request)
            except Exception as gemini_error:
                print("Gemini failed, falling back to smart chat")
                chat_response = await chat_service.smart_chat(chat_request)
                chat_response.response = f"[Note: Using fallback model due to Gemini unavailability]\n\n{chat_response.response}"
        elif model == "Ollama":
            try:
                chat_response = await chat_service.chat_with_ollama(chat_request)
            except Exception as ollama_error:
                print("Ollama failed, falling back to smart chat")
                chat_response = await chat_service.smart_chat(chat_request)
                chat_response.response = f"[Note: Using fallback model due to Ollama unavailability]\n\n{chat_response.response}"
        else:
            # Default to smart chat for any other model names
            chat_response = await chat_service.smart_chat(chat_request)
            
        # Add AI response to session
        session_service.add_message(MessageCreate(
            session_id=session_id,
            role="assistant",
            content=chat_response.response
        ))
        
        # Return combined response
        return {
            "session_id": session_id,
            "response": chat_response.response,
            "sources": chat_response.sources if hasattr(chat_response, "sources") else [],
            "model": model
        }
        
    except Exception as e:
        print(f"Chat with session error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/chat/folder/{folder_id}/indexed")
async def check_folder_files_indexed(
    folder_id: UUID4,
    supabase=Depends(get_supabase),
    chat_service=Depends(get_chat_service)
):
    """Check if all files in a folder are indexed and ready for querying"""
    try:
        # Get all files from the folder
        file_service = FileService(supabase)
        files = file_service.get_folder_files(folder_id)
        
        if not files:
            return {"indexed": True, "message": "No files to index"}
        
        # Vector storage info
        from vector_store import VectorStore
        vector_store = VectorStore(supabase_client=supabase)
        storage_info = await vector_store.get_storage_info()
        
        # Check each file
        for file in files:
            file_id = file.id
            # Try a simple search query limited to this file to see if it's indexed
            results = await vector_store.similarity_search(
                "test",
                k=1,
                filter_dict={"file_id": str(file_id)}
            )
            
            # If any file is not indexed, return false
            if not results:
                return {
                    "indexed": False, 
                    "message": f"File {file.original_filename} is not indexed yet",
                    "storage": storage_info.get("primary_storage")
                }
        
        # All files are indexed
        return {
            "indexed": True,
            "message": "All files are indexed and ready",
            "storage": storage_info.get("primary_storage")
        }
        
    except Exception as e:
        print(f"Error checking indexed status: {str(e)}")
        # Default to True to avoid blocking the UI unnecessarily
        return {"indexed": True, "message": f"Error checking status: {str(e)}"}