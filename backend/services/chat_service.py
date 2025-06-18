import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_qdrant import Qdrant
from typing import List, Tuple
from services.document_service import DocumentService
from models.schemas import ChatRequest, ChatResponse


class ChatService:
    """Service for chat operations with documents"""
    
    def __init__(self, supabase, embeddings, llm, qdrant_client, sentence_model):
        self.supabase = supabase
        self.embeddings = embeddings
        self.llm = llm
        self.qdrant_client = qdrant_client
        self.sentence_model = sentence_model
        self.document_service = DocumentService()
    
    def get_folder_files(self, folder_id: str) -> List[dict]:
        """Get all files in a folder"""
        files_response = self.supabase.table("folder_files").select(
            "files(*)"
        ).eq("folder_id", folder_id).execute()
        
        if not files_response.data:
            raise Exception("No files found in this folder")
        
        return [item["files"] for item in files_response.data if item["files"]]
    
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
    
    def chat_with_openai(self, request: ChatRequest) -> ChatResponse:
        """Chat with documents using OpenAI"""
        try:
            # Check if OpenAI is available
            if self.llm is None or self.embeddings is None:
                print("OpenAI not available, falling back to simple chat")
                return self.simple_chat(request)
            
            # Get files from folder
            files = self.get_folder_files(str(request.folder_id))
            
            # Process files to extract text
            all_texts, sources = self.document_service.process_files_to_text(files)
            
            if not all_texts:
                raise Exception("No readable text found in PDFs")
            
            # Split text into chunks
            chunks, chunk_sources = self.document_service.split_texts_to_chunks(all_texts, sources)
            
            # Create or get vector store
            vector_store = self.create_or_get_vector_store(str(request.folder_id), chunks, chunk_sources)
            
            # Search for relevant chunks
            relevant_docs = vector_store.similarity_search(request.message, k=3)
            
            # Build context from relevant documents
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            relevant_sources = list(set([doc.metadata.get("source", "Unknown") for doc in relevant_docs]))
            
            # Generate response
            prompt = f"""Based on the following context from the uploaded documents, please answer the question.
            
Context:
{context}

Question: {request.message}

Please provide a helpful and accurate answer based on the context provided. If the answer cannot be found in the context, please say so."""

            response = self.llm.invoke(prompt)
            
            return ChatResponse(
                response=response.content,
                sources=relevant_sources
            )
            
        except Exception as e:
            # Check for quota errors specifically
            error_str = str(e).lower()
            if 'quota' in error_str or 'insufficient_quota' in error_str or '429' in error_str:
                raise Exception(f"OpenAI quota exceeded: {str(e)}")
            else:
                raise Exception(f"Chat failed: {str(e)}")
            
            
    def simple_chat(self, request: ChatRequest) -> ChatResponse:
        """Simple chat without OpenAI - uses local embeddings and basic matching"""
        try:
            # Get files from folder
            files = self.get_folder_files(str(request.folder_id))
            
            # Process files to extract text
            all_texts, sources = self.document_service.process_files_to_text(files)
            
            if not all_texts:
                raise Exception("No readable text found in PDFs")
            
            # Split text into chunks
            chunks, chunk_sources = self.document_service.split_texts_to_chunks(all_texts, sources)
            
            # Create embeddings for chunks and query
            chunk_embeddings = self.sentence_model.encode(chunks)
            query_embedding = self.sentence_model.encode([request.message])
            
            # Find most similar chunks
            similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
            top_indices = np.argsort(similarities)[-3:][::-1]  # Top 3 most similar
            
            # Get relevant chunks
            relevant_chunks = [chunks[i] for i in top_indices if similarities[i] > 0.1]
            relevant_sources = list(set([chunk_sources[i] for i in top_indices if similarities[i] > 0.1]))
            
            if not relevant_chunks:
                return ChatResponse(
                    response="I couldn't find relevant information in the uploaded documents to answer your question.",
                    sources=sources
                )
            
            # Simple response generation (without LLM)
            context = "\n\n".join(relevant_chunks[:2])  # Use top 2 chunks
            
            response_text = f"""Based on the uploaded documents, here are the most relevant excerpts:

{context}

Question: {request.message}

The above content from your documents seems most relevant to your question. Please review the excerpts for specific details."""
            
            return ChatResponse(
                response=response_text,
                sources=relevant_sources
            )
            
        except Exception as e:
            raise Exception(f"Simple chat failed: {str(e)}") 