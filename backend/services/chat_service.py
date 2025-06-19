import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_qdrant import Qdrant
from typing import List, Tuple, Dict
from services.document_service import DocumentService
from models.schemas import ChatRequest, ChatResponse
from openai import OpenAI
import google.generativeai as genai
import requests
import json
from rag import RAGChat
from config import config
from dependencies import check_openai_api_key, check_gemini_api_key, check_ollama_availability
from vector_store import VectorStore
import asyncio

class ChatService:
    """Service for chat operations with documents"""
    
    def __init__(self, supabase, embeddings, llm, qdrant_client, gemini_model=None):
        self.supabase = supabase
        self.embeddings = embeddings
        self.llm = llm
        self.qdrant_client = qdrant_client
        self.gemini_model = gemini_model
        self.document_service = DocumentService()
        
        # Initialize vector store (can be configured to use Supabase or Qdrant)
        self.vector_store = VectorStore(supabase_client=supabase)
    
    def get_folder_files(self, folder_id: str) -> List[dict]:
        """Get all files in a folder"""
        files_response = self.supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", folder_id).execute()
        
        if not files_response.data:
            raise Exception("No files found in this folder")
        
        return [item["files"] for item in files_response.data if item["files"]]
    
    async def ensure_files_are_indexed(self, folder_id: str, files: List[dict]):
        """Ensure all files in folder are properly indexed in vector store"""
        for file_info in files:
            file_id = file_info['id']
            
            # Check if file is already indexed
            test_results = await self.vector_store.similarity_search(
                "test query",
                k=1,
                filter_dict={"file_id": file_id}
            )
            
            if not test_results:
                print(f"File {file_info['original_filename']} not found in vector store. Processing...")
                
                # Process and index the file
                from document_processor import DocumentProcessor
                processor = DocumentProcessor(self.supabase)
                
                chunks = await processor.process_pdf(
                    file_info['storage_path'],
                    file_id,
                    folder_id,
                    file_info['original_filename']
                )
                
                if chunks:
                    await self.vector_store.add_documents(chunks, file_id)
                    print(f"Indexed {len(chunks)} chunks for {file_info['original_filename']}")
    
    def create_or_get_vector_store(self, folder_id: str, chunks: List[str], chunk_sources: List[str]):
        """Create or get existing vector store for folder"""
        collection_name = f"folder_{folder_id.replace('-', '_')}"
        
        # Check if collection exists, if not create vector store
        try:
            self.qdrant_client.get_collection(collection_name)
        except:
            # Create vector store with chunks
            Qdrant.from_texts(
                chunks,
                self.embeddings,
                client=self.qdrant_client,
                collection_name=collection_name,
                metadatas=[{"source": source} for source in chunk_sources]
            )
        
        # Initialize vector store for querying
        return Qdrant(
            client=self.qdrant_client,
            collection_name=collection_name,
            embeddings=self.embeddings
        )
    
    def determine_best_model(self) -> str:
        """
        Determine the best available model based on API key availability.
        Priority: OpenAI -> Gemini -> Ollama -> Simple (local)
        """
        if check_openai_api_key():
            return "openai"
        elif check_gemini_api_key():
            return "gemini"
        elif check_ollama_availability():
            return "ollama"
        else:
            return "unavailable"
    
    async def search_relevant_content(self, query: str, folder_id: str, k: int = 5) -> Tuple[List[str], List[str], List[str]]:
        """Search for relevant content using vector store"""
        # Search using vector store
        results = await self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter_dict={"folder_id": folder_id}
        )
        
        # Extract content and sources
        relevant_chunks = []
        relevant_sources = []
        all_sources = []
        
        for doc, score in results:
            if score > 0.3:  # Relevance threshold
                relevant_chunks.append(doc.page_content)
                source = doc.metadata.get('filename', doc.metadata.get('source', 'Unknown'))
                relevant_sources.append(source)
            all_sources.append(doc.metadata.get('filename', doc.metadata.get('source', 'Unknown')))
        
        # Remove duplicates while preserving order
        relevant_sources = list(dict.fromkeys(relevant_sources))
        all_sources = list(dict.fromkeys(all_sources))
        
        return relevant_chunks, relevant_sources, all_sources
    
    async def chat_with_gemini(self, request: ChatRequest) -> ChatResponse:
        """Chat with documents using Google Gemini"""
        try:
            if self.gemini_model is None:
                # Search for relevant content without AI processing
                files = self.get_folder_files(str(request.folder_id))
                await self.ensure_files_are_indexed(str(request.folder_id), files)
                relevant_chunks, relevant_sources, all_sources = await self.search_relevant_content(
                    request.message, str(request.folder_id)
                )
                
                error_msg = "Google Gemini is not available. Please check your API key configuration."
                if relevant_chunks:
                    response_text = f"{error_msg}\n\nHowever, I found these potentially relevant excerpts from your documents:\n\n"
                    response_text += "\n\n".join(relevant_chunks[:2])  # Show top 2 chunks
                    return ChatResponse(
                        response=response_text,
                        sources=relevant_sources,
                        model="Unavailable"
                    )
                else:
                    return ChatResponse(
                        response=f"{error_msg} Additionally, I couldn't find relevant information in the documents for your query.",
                        sources=all_sources,
                        model="Unavailable"
                    )
            
            # Get files from folder
            files = self.get_folder_files(str(request.folder_id))
            
            # Ensure files are indexed
            await self.ensure_files_are_indexed(str(request.folder_id), files)
            
            # Search for relevant content
            relevant_chunks, relevant_sources, all_sources = await self.search_relevant_content(
                request.message, str(request.folder_id)
            )
            
            if not relevant_chunks:
                return ChatResponse(
                    response="I couldn't find relevant information in the uploaded documents to answer your question.",
                    sources=all_sources
                )
            
            # Build context from relevant documents
            context = "\n\n".join(relevant_chunks[:3])  # Use top 3 chunks
            
            # Generate response with Gemini
            prompt = f"""Based on the following context from the uploaded documents, please answer the question.
            
            Context:
            {context}

            Question: {request.message}

            Please provide a helpful and accurate answer based on the context provided. If the answer cannot be found in the context, please say so."""

            response = self.gemini_model.generate_content(prompt)
            
            return ChatResponse(
                response=response.text,
                sources=relevant_sources
            )
            
        except Exception as e:
            raise Exception(f"Gemini chat failed: {str(e)}")
    
    async def chat_with_ollama(self, request: ChatRequest) -> ChatResponse:
        """Chat with documents using Ollama local LLM"""
        try:
            # Get files from folder
            files = self.get_folder_files(str(request.folder_id))
            
            # Ensure files are indexed
            await self.ensure_files_are_indexed(str(request.folder_id), files)
            
            # Search for relevant content
            relevant_chunks, relevant_sources, all_sources = await self.search_relevant_content(
                request.message, str(request.folder_id)
            )
            
            if not relevant_chunks:
                return ChatResponse(
                    response="I couldn't find relevant information in the uploaded documents to answer your question.",
                    sources=all_sources
                )
            
            # Build context from relevant documents
            context = "\n\n".join(relevant_chunks[:3])  # Use top 3 chunks
            
            # Prepare messages for Ollama
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided document context. Always base your answers on the given context."
                },
                {
                    "role": "user",
                    "content": f"""Based on the following context from the uploaded documents, please answer the question.
            
                Context:
                {context}
                
                Question: {request.message}

                Please provide a helpful and accurate answer based on the context provided. If the answer cannot be found in the context, please say so."""
                }
            ]
            
            # Call Ollama API
            response = requests.post(
                f"{config.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": config.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            return ChatResponse(
                response=result.get("message", {}).get("content", "No response generated"),
                sources=relevant_sources
            )
            
        except Exception as e:
            raise Exception(f"Ollama chat failed: {str(e)}")
    
    async def chat_with_openai(self, request: ChatRequest) -> ChatResponse:
        """Chat with documents using OpenAI"""
        try:
            # Check if OpenAI is available
            if self.llm is None or self.embeddings is None:
                # Search for relevant content without AI processing
                files = self.get_folder_files(str(request.folder_id))
                await self.ensure_files_are_indexed(str(request.folder_id), files)
                relevant_chunks, relevant_sources, all_sources = await self.search_relevant_content(
                    request.message, str(request.folder_id)
                )
                
                error_msg = "OpenAI is not available. Please check your API key configuration."
                if relevant_chunks:
                    response_text = f"{error_msg}\n\nHowever, I found these potentially relevant excerpts from your documents:\n\n"
                    response_text += "\n\n".join(relevant_chunks[:2])  # Show top 2 chunks
                    return ChatResponse(
                        response=response_text,
                        sources=relevant_sources,
                        model="Unavailable"
                    )
                else:
                    return ChatResponse(
                        response=f"{error_msg} Additionally, I couldn't find relevant information in the documents for your query.",
                        sources=all_sources,
                        model="Unavailable"
                    )
            
            # Get files from folder
            files = self.get_folder_files(str(request.folder_id))
            
            # Ensure files are indexed
            await self.ensure_files_are_indexed(str(request.folder_id), files)
            
            # Use RAG approach with vector store
            rag_chat = RAGChat(self.vector_store)
            
            result = await rag_chat.chat(
                message=request.message,
                folder_id=str(request.folder_id),
                k=5
            )
            
            return ChatResponse(
                response=result["answer"],
                sources=[source["metadata"].get("filename", "Unknown") for source in result["sources"]]
            )
            
        except Exception as e:
            # Check for quota errors specifically
            error_str = str(e).lower()
            if 'quota' in error_str or 'insufficient_quota' in error_str or '429' in error_str:
                raise Exception(f"OpenAI quota exceeded: {str(e)}")
            else:
                raise Exception(f"Chat failed: {str(e)}")
    
    async def smart_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Intelligent chat that automatically selects the best available model.
        Priority: OpenAI -> Gemini -> Ollama
        """
        best_model = self.determine_best_model()
        
        # Handle case when no models are available
        if best_model == "unavailable":
            # Get files from folder to retrieve relevant chunks
            files = self.get_folder_files(str(request.folder_id))
            
            # Ensure files are indexed
            await self.ensure_files_are_indexed(str(request.folder_id), files)
            
            # Search for relevant content
            relevant_chunks, relevant_sources, all_sources = await self.search_relevant_content(
                request.message, str(request.folder_id), k=5
            )
            
            if not relevant_chunks:
                return ChatResponse(
                    response="I couldn't find relevant information in your documents. Additionally, no AI models are currently available to process your question. Please check your API keys and connections.",
                    sources=all_sources,
                    model="Unavailable"
                )
            
            # Return response with relevant chunks but no AI-generated text
            response_text = f"""No AI models are currently available to process your question. Please check your API keys and connections.
            
However, I found these potentially relevant excerpts from your documents:

{relevant_chunks[0] if relevant_chunks else "No relevant content found."}"""
            
            if len(relevant_chunks) > 1:
                response_text += f"\n\n{relevant_chunks[1]}"
            
            return ChatResponse(
                response=response_text,
                sources=relevant_sources,
                model="Unavailable"
            )
        
        try:
            if best_model == "openai":
                print("Using OpenAI model for chat")
                return await self.chat_with_openai(request)
            elif best_model == "gemini":
                print("Using Gemini model for chat")
                return await self.chat_with_gemini(request)
            elif best_model == "ollama":
                print("Using Ollama model for chat")
                return await self.chat_with_ollama(request)
            
        except Exception as e:
            # If the selected model fails, try fallback models
            print(f"Primary model ({best_model}) failed: {str(e)}")
            
            if best_model == "openai":
                try:
                    print("Falling back to Gemini")
                    return await self.chat_with_gemini(request)
                except Exception as gemini_error:
                    try:
                        print(f"Gemini also failed: {str(gemini_error)}, falling back to Ollama")
                        return await self.chat_with_ollama(request)
                    except Exception as ollama_error:
                        print(f"Ollama also failed: {str(ollama_error)}")
                        raise Exception("All AI models failed. Please check your API keys and connections.")
            elif best_model == "gemini":
                try:
                    print("Falling back to Ollama")
                    return await self.chat_with_ollama(request)
                except Exception as ollama_error:
                    print(f"Ollama also failed: {str(ollama_error)}")
                    raise Exception("All AI models failed. Please check your API keys and connections.")
            else:
                raise Exception(f"All models failed: {str(e)}")