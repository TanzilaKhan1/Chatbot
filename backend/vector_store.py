from typing import List, Dict, Any, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import config

class VectorStore:
    def __init__(self):
        # Initialize Qdrant client
        if config.QDRANT_API_KEY:
            # Cloud deployment
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT,
                api_key=config.QDRANT_API_KEY
            )
        else:
            # Local deployment
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT
            )
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize collection
        self._init_collection()
        
        # Initialize Langchain vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            embedding=self.embeddings,
        )
    
    def _init_collection(self):
        """Initialize Qdrant collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if config.QDRANT_COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=config.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=config.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                ),
            )
            print(f"Created collection: {config.QDRANT_COLLECTION_NAME}")
    
    async def add_documents(self, documents: List[Document], file_id: str) -> List[str]:
        """Add documents to vector store"""
        # Generate IDs for documents
        ids = [str(uuid.uuid4()) for _ in documents]
        
        # Add file_id to metadata
        for doc in documents:
            doc.metadata["file_id"] = file_id
        
        # Add documents to vector store
        self.vector_store.add_documents(
            documents=documents,
            ids=ids
        )
        
        return ids
    
    async def delete_by_file_id(self, file_id: str):
        """Delete all vectors associated with a file"""
        # Search for all points with the given file_id
        results = self.client.scroll(
            collection_name=config.QDRANT_COLLECTION_NAME,
            scroll_filter={
                "must": [
                    {
                        "key": "metadata.file_id",
                        "match": {"value": file_id}
                    }
                ]
            },
            limit=1000
        )
        
        # Extract point IDs
        point_ids = [point.id for point in results[0]]
        
        if point_ids:
            # Delete points
            self.client.delete(
                collection_name=config.QDRANT_COLLECTION_NAME,
                points_selector=point_ids
            )
            print(f"Deleted {len(point_ids)} vectors for file {file_id}")
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents"""
        if filter_dict:
            # Build Qdrant filter
            must_conditions = []
            for key, value in filter_dict.items():
                must_conditions.append({
                    "key": f"metadata.{key}",
                    "match": {"value": value}
                })
            
            search_kwargs = {
                "k": k,
                "filter": {"must": must_conditions}
            }
        else:
            search_kwargs = {"k": k}
        
        # Perform similarity search
        results = self.vector_store.similarity_search(
            query=query,
            **search_kwargs
        )
        
        return results
    
    async def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """Search for similar documents with relevance scores"""
        if filter_dict:
            # Build Qdrant filter
            must_conditions = []
            for key, value in filter_dict.items():
                must_conditions.append({
                    "key": f"metadata.{key}",
                    "match": {"value": value}
                })
            
            search_kwargs = {
                "k": k,
                "filter": {"must": must_conditions}
            }
        else:
            search_kwargs = {"k": k}
        
        # Perform similarity search with scores
        results = self.vector_store.similarity_search_with_score(
            query=query,
            **search_kwargs
        )
        
        return results
    
    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """Get a retriever for the vector store"""
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs
        )