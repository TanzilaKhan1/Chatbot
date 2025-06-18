from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import UUID4
from models.schemas import ChatRequest, ChatResponse, FileResponse, SessionCreate, MessageCreate
from services.chat_service import ChatService
from services.file_service import FileService
from services.session_service import SessionService
from dependencies import get_supabase, get_embeddings, get_llm, get_qdrant_client, get_sentence_model

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
    qdrant_client=Depends(get_qdrant_client),
    sentence_model=Depends(get_sentence_model)
):
    """Chat with documents in a folder using AI"""
    try:
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, sentence_model)
        return chat_service.chat_with_openai(request)
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")



@router.post("/chat/simple", response_model=ChatResponse)
async def simple_chat_with_documents(
    request: ChatRequest,
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client),
    sentence_model=Depends(get_sentence_model)
):
    """Simple chat without OpenAI - uses local embeddings and basic matching"""
    try:
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, sentence_model)
        return chat_service.simple_chat(request)
    except Exception as e:
        print(f"Simple chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/chat/simple/health")
async def simple_chat_health(sentence_model=Depends(get_sentence_model)):
    """Check if simple chat is working"""
    try:
        # Test sentence transformer
        test_embedding = sentence_model.encode(["test"])
        return {
            "status": "healthy",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": len(test_embedding[0])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 
        


@router.post("/chat/with-session", response_model=dict)
async def chat_with_session(
    message: str,
    folder_id: UUID4,
    session_id: Optional[UUID4] = None,
    model: str = "OpenAI",
    supabase=Depends(get_supabase),
    embeddings=Depends(get_embeddings),
    llm=Depends(get_llm),
    qdrant_client=Depends(get_qdrant_client),
    sentence_model=Depends(get_sentence_model)
):
    """Chat with documents and maintain session history"""
    try:
        session_service = SessionService(supabase)
        chat_service = ChatService(supabase, embeddings, llm, qdrant_client, sentence_model)
        
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
        
        # Try OpenAI first if selected
        if model == "OpenAI":
            try:
                chat_response = chat_service.chat_with_openai(chat_request)
            except Exception as openai_error:
                # Check if it's a quota error
                error_str = str(openai_error).lower()
                if 'quota' in error_str or 'insufficient_quota' in error_str or '429' in error_str:
                    print("OpenAI quota exceeded, falling back to simple chat")
                    # Fall back to simple chat
                    chat_response = chat_service.simple_chat(chat_request)
                    # Optionally update the session model to reflect the fallback
                    # You might want to notify the user that we're using the fallback model
                    chat_response.response = f"[Note: Using local model due to OpenAI quota limits]\n\n{chat_response.response}"
                else:
                    # Re-raise if it's not a quota error
                    raise
        else:
            # Use simple chat (Gemini/Local model)
            chat_response = chat_service.simple_chat(chat_request)
        
        # Add assistant message to session
        session_service.add_message(MessageCreate(
            session_id=session_id,
            role="assistant",
            content=chat_response.response
        ))
        
        return {
            "session_id": str(session_id),
            "response": chat_response.response,
            "sources": chat_response.sources
        }
        
    except Exception as e:
        print(f"Chat with session error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    