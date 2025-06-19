from typing import List, Dict, Any, Optional, Tuple
import uuid
import numpy as np
from datetime import datetime
import asyncio
import json
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from supabase import Client

from config import config

class VectorStore:
    def __init__(self, supabase_client: Client = None, use_supabase_vectors: bool = None):
        self.supabase = supabase_client
        self.supabase_available = False
        self.qdrant_available = False
        
        # Set use_supabase_vectors from parameter or config
        self.use_supabase_vectors = use_supabase_vectors
        if self.use_supabase_vectors is None:
            self.use_supabase_vectors = config.USE_SUPABASE_VECTORS if hasattr(config, 'USE_SUPABASE_VECTORS') else False
        
        # Initialize HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.embedding_dimension = config.EMBEDDING_DIMENSION
        print("Using HuggingFace embeddings")
        
        # Try to initialize Supabase vectors first if enabled
        if supabase_client and self.use_supabase_vectors:
            self.supabase_available = self._init_supabase_vectors()
            print(f"Supabase vector storage available: {self.supabase_available}")
        
        # Always initialize Qdrant as backup
        self.qdrant_available = self._init_qdrant()
        
        if not self.supabase_available and not self.qdrant_available:
            raise Exception("Both Supabase and Qdrant vector stores failed to initialize")
    
    def _check_supabase_connection(self) -> bool:
        """Check if Supabase is currently accessible"""
        if not self.supabase:
            return False
        
        try:
            # Try a simple query to test connection
            self.supabase.table('folders').select('id').limit(1).execute()
            return True
        except Exception as e:
            print(f"Supabase connection check failed: {e}")
            return False
    
    def _init_supabase_vectors(self) -> bool:
        """Initialize Supabase vector storage using pgvector"""
        try:
            # First check if we can connect to Supabase
            if not self._check_supabase_connection():
                print("Supabase is not accessible")
                return False
            
            # Check if pgvector extension is installed
            try:
                # Check if the document_vectors table exists
                response = self.supabase.table('document_vectors').select('id').limit(1).execute()
                print("Document vectors table found in Supabase")
            except Exception as e:
                print(f"Error accessing document_vectors table: {e}")
                print("Please ensure the pgvector extension is installed and document_vectors table is created")
                return False
                
            # Verify vector_search function exists by testing it
            try:
                # Create a test embedding (all zeros)
                test_embedding = [0.0] * config.EMBEDDING_DIMENSION
                
                # Try calling the vector_search function
                response = self.supabase.rpc('vector_search', {
                    'query_embedding': test_embedding,
                    'match_count': 1
                }).execute()
                
                print("Vector search function verified in Supabase")
            except Exception as e:
                print(f"Error with vector_search function: {e}")
                print("Please ensure the vector_search function is properly created")
                return False
            
            print("Supabase vector storage initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Supabase vectors: {e}")
            return False
    
    def _init_qdrant(self) -> bool:
        """Initialize Qdrant vector store"""
        try:
            # Initialize Qdrant client
            if config.QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    host=config.QDRANT_HOST,
                    port=config.QDRANT_PORT,
                    api_key=config.QDRANT_API_KEY
                )
            else:
                self.qdrant_client = QdrantClient(
                    host=config.QDRANT_HOST,
                    port=config.QDRANT_PORT
                )
            
            # Initialize collection
            self._init_qdrant_collection()
            
            # Initialize Langchain vector store
            self.qdrant_vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=config.QDRANT_COLLECTION_NAME,
                embedding=self.embeddings,
            )
            
            print("Qdrant vector storage initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Qdrant: {e}")
            return False
    
    def _init_qdrant_collection(self):
        """Initialize Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if config.QDRANT_COLLECTION_NAME not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    ),
                )
                print(f"Created Qdrant collection: {config.QDRANT_COLLECTION_NAME}")
        except Exception as e:
            print(f"Error initializing Qdrant collection: {e}")
            raise
    
    async def add_documents(self, documents: List[Document], file_id: str) -> List[str]:
        """Add documents to vector store with automatic fallback"""
        if not documents:
            print(f"No documents to add for file {file_id}")
            return []
        
        # Validate and prepare documents
        valid_documents = []
        for doc in documents:
            if doc.page_content and len(doc.page_content.strip()) > 0:
                doc.metadata["file_id"] = file_id
                valid_documents.append(doc)
        
        if not valid_documents:
            print(f"No valid documents after filtering for file {file_id}")
            return []
        
        print(f"Adding {len(valid_documents)} documents for file {file_id}")
        
        ids = []
        supabase_success = False
        qdrant_success = False
        
        # Try Supabase first if available
        if self.supabase_available and self._check_supabase_connection():
            try:
                ids = await self._add_documents_supabase(valid_documents)
                supabase_success = True
                print(f"Successfully added documents to Supabase for file {file_id}")
            except Exception as e:
                print(f"Failed to add documents to Supabase: {e}")
                supabase_success = False
        
        # Add to Qdrant if Supabase failed
        if not supabase_success:
            if self.qdrant_available:
                try:
                    qdrant_ids = await self._add_documents_qdrant(valid_documents)
                    ids = qdrant_ids
                    qdrant_success = True
                    print(f"Successfully added documents to Qdrant for file {file_id}")
                except Exception as e:
                    print(f"Failed to add documents to Qdrant: {e}")
                    qdrant_success = False
                    
                
        if not supabase_success and not qdrant_success:
            raise Exception("Failed to add documents to both Supabase and Qdrant")
        
        return ids
    
    async def _add_documents_supabase(self, documents: List[Document]) -> List[str]:
        """Add documents to Supabase using pgvector"""
        ids = []
        
        try:
            # Generate embeddings in batches
            batch_size = 50
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                texts = [doc.page_content for doc in batch_docs]
                
                # Generate embeddings
                embeddings = self.embeddings.embed_documents(texts)
                
                # Prepare data for insertion
                rows = []
                for j, (doc, embedding) in enumerate(zip(batch_docs, embeddings)):
                    chunk_id = doc.metadata.get('chunk_id', str(uuid.uuid4()))
                    
                    # Prepare row data
                    row_data = {
                        'file_id': doc.metadata['file_id'],
                        'folder_id': doc.metadata['folder_id'],
                        'content': doc.page_content,
                        'metadata': json.dumps(doc.metadata),  # Convert to JSON string
                        'embedding': embedding,
                        'chunk_index': doc.metadata.get('chunk_index', j),
                        'chunk_id': chunk_id,
                        'page_number': doc.metadata.get('page', None),
                        'total_pages': doc.metadata.get('total_pages', None),
                        'extraction_method': doc.metadata.get('extraction_method', 'unknown')
                    }
                    rows.append(row_data)
                    ids.append(chunk_id)
                
                # Insert into Supabase
                response = self.supabase.table('document_vectors').insert(rows).execute()
                
                if not response.data:
                    raise Exception("Failed to insert documents into Supabase")
                
                print(f"Added batch {i//batch_size + 1} to Supabase ({len(rows)} docs)")
            
            return ids
            
        except Exception as e:
            print(f"Error adding documents to Supabase: {e}")
            raise
    
    async def _add_documents_qdrant(self, documents: List[Document]) -> List[str]:
        """Add documents to Qdrant"""
        ids = [str(uuid.uuid4()) for _ in documents]
        
        try:
            # Add documents in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.qdrant_vector_store.add_documents(
                    documents=batch_docs,
                    ids=batch_ids
                )
                print(f"Added batch {i//batch_size + 1} to Qdrant ({len(batch_docs)} docs)")
            
            return ids
        except Exception as e:
            print(f"Error adding documents to Qdrant: {e}")
            raise
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents with automatic fallback"""
        results = []
        supabase_success = False
        qdrant_success = False
        
        # Try Supabase first if available
        if self.supabase_available and self._check_supabase_connection():
            try:
                results = await self._search_supabase(query, k, filter_dict)
                if results:
                    supabase_success = True
                    return results
            except Exception as e:
                print(f"Supabase search failed: {e}")
                supabase_success = False
        
        # Try Qdrant if Supabase failed
        if self.qdrant_available:
            try:
                results = await self._search_qdrant(query, k, filter_dict)
                qdrant_success = True
            except Exception as e:
                print(f"Qdrant search failed: {e}")
                qdrant_success = False
                
        if not supabase_success and not qdrant_success:
            raise Exception("Both Supabase and Qdrant searches failed")
        
        return results
    
    async def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with relevance scores"""
        results = []
        supabase_success = False
        qdrant_success = False
        
        # Try Supabase first if available
        if self.supabase_available and self._check_supabase_connection():
            try:
                results = await self._search_with_score_supabase(query, k, filter_dict)
                if results:
                    supabase_success = True
                    return results
            except Exception as e:
                print(f"Supabase search with score failed: {e}")
                supabase_success = False
        
        # Fallback to Qdrant
        if self.qdrant_available:
            try:
                results = await self._search_with_score_qdrant(query, k, filter_dict)
                qdrant_success = True
            except Exception as e:
                print(f"Qdrant search with score failed: {e}")
                qdrant_success = False
                
        if not supabase_success and not qdrant_success:
            raise Exception("Both Supabase and Qdrant searches failed")
        
        return results
    
    async def _search_supabase(
        self,
        query: str,
        k: int,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search using Supabase pgvector"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Prepare parameters for the function call
            params = {
                'query_embedding': query_embedding,
                'match_count': k
            }
            
            if filter_dict:
                if 'file_id' in filter_dict:
                    params['filter_file_id'] = filter_dict['file_id']
                if 'folder_id' in filter_dict:
                    params['filter_folder_id'] = filter_dict['folder_id']
            
            # Call the vector_search function
            response = self.supabase.rpc('vector_search', params).execute()
            
            if not response.data:
                return []
            
            # Convert results to Document objects
            documents = []
            for row in response.data:
                # Parse metadata if it's a string
                metadata = row['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                doc = Document(
                    page_content=row['content'],
                    metadata=metadata
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Supabase search error: {e}")
            raise
    
    async def _search_with_score_supabase(
        self,
        query: str,
        k: int,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Search with scores using Supabase pgvector"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Prepare parameters
            params = {
                'query_embedding': query_embedding,
                'match_count': k
            }
            
            if filter_dict:
                if 'file_id' in filter_dict:
                    params['filter_file_id'] = filter_dict['file_id']
                if 'folder_id' in filter_dict:
                    params['filter_folder_id'] = filter_dict['folder_id']
            
            # Call the vector_search function
            response = self.supabase.rpc('vector_search', params).execute()
            
            if not response.data:
                return []
            
            # Convert results to Document objects with scores
            results = []
            for row in response.data:
                # Parse metadata if it's a string
                metadata = row['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                doc = Document(
                    page_content=row['content'],
                    metadata=metadata
                )
                similarity = row['similarity']
                results.append((doc, similarity))
            
            return results
            
        except Exception as e:
            print(f"Supabase search with score error: {e}")
            raise
    
    async def _search_qdrant(
        self,
        query: str,
        k: int,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search using Qdrant"""
        if filter_dict:
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
        
        results = self.qdrant_vector_store.similarity_search(
            query=query,
            **search_kwargs
        )
        
        return results
    
    async def _search_with_score_qdrant(
        self,
        query: str,
        k: int,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Search with scores using Qdrant"""
        if filter_dict:
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
        
        results = self.qdrant_vector_store.similarity_search_with_score(
            query=query,
            **search_kwargs
        )
        
        return results
    
    async def delete_by_file_id(self, file_id: str):
        """Delete all vectors associated with a file from both stores"""
        errors = []
        
        # Try to delete from Supabase
        if self.supabase_available and self._check_supabase_connection():
            try:
                await self._delete_supabase_vectors(file_id)
                print(f"Deleted vectors for file {file_id} from Supabase")
            except Exception as e:
                errors.append(f"Supabase deletion failed: {e}")
        
        # Try to delete from Qdrant
        if self.qdrant_available:
            try:
                await self._delete_qdrant_vectors(file_id)
                print(f"Deleted vectors for file {file_id} from Qdrant")
            except Exception as e:
                errors.append(f"Qdrant deletion failed: {e}")
        
        if errors and len(errors) == 2:
            raise Exception(f"Failed to delete from both stores: {'; '.join(errors)}")
    
    async def _delete_supabase_vectors(self, file_id: str):
        """Delete vectors from Supabase"""
        response = self.supabase.table('document_vectors').delete().eq('file_id', file_id).execute()
        if not response.data and hasattr(response, 'error') and response.error:
            raise Exception(f"Supabase deletion error: {response.error}")
    
    async def _delete_qdrant_vectors(self, file_id: str):
        """Delete vectors from Qdrant"""
        filter_condition = Filter(
            must=[
                FieldCondition(
                    key="metadata.file_id",
                    match=MatchValue(value=file_id)
                )
            ]
        )
        
        self.qdrant_client.delete(
            collection_name=config.QDRANT_COLLECTION_NAME,
            points_selector=filter_condition
        )
    
    
    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """Get a retriever for the vector store"""
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        # Create a custom retriever that handles fallback
        from langchain_core.retrievers import BaseRetriever
        
        class FallbackRetriever(BaseRetriever):
            def __init__(self, vector_store, search_kwargs):
                self.vector_store = vector_store
                self.search_kwargs = search_kwargs
            
            async def _aget_relevant_documents(self, query: str) -> List[Document]:
                filter_dict = None
                if 'filter' in self.search_kwargs and isinstance(self.search_kwargs['filter'], dict):
                    # Extract filter conditions
                    filter_dict = {}
                    if 'must' in self.search_kwargs['filter']:
                        for condition in self.search_kwargs['filter']['must']:
                            key = condition.get('key', '').replace('metadata.', '')
                            value = condition.get('match', {}).get('value')
                            if key and value:
                                filter_dict[key] = value
                
                return await self.vector_store.similarity_search(
                    query, 
                    k=self.search_kwargs.get('k', 5),
                    filter_dict=filter_dict
                )
            
            def _get_relevant_documents(self, query: str) -> List[Document]:
                import asyncio
                return asyncio.run(self._aget_relevant_documents(query))
        
        return FallbackRetriever(self, search_kwargs)