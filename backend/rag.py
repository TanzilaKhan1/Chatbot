from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from config import config
from vector_store import VectorStore

class RAGChat:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=0.7,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that answers questions based on the provided PDF documents. 
            Use the following context to answer the user's question. If you cannot find the answer in the context, 
            say so honestly. Always cite the source document when providing information.
            
            Context: {context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Create document chain
        self.document_chain = create_stuff_documents_chain(self.llm, self.prompt)
    
    async def chat(
        self,
        message: str,
        chat_history: List[Dict[str, str]] = None,
        folder_id: Optional[str] = None,
        file_id: Optional[str] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Process a chat message and return response with sources
        
        Args:
            message: User's question
            chat_history: Previous conversation history
            folder_id: Filter by specific folder
            file_id: Filter by specific file
            k: Number of relevant documents to retrieve
        """
        # Build filter
        filter_dict = {}
        if folder_id:
            filter_dict["folder_id"] = folder_id
        if file_id:
            filter_dict["file_id"] = file_id
        
        # Get retriever with filter
        retriever = self.vector_store.get_retriever(
            search_kwargs={
                "k": k,
                "filter": {"must": [
                    {"key": f"metadata.{key}", "match": {"value": value}}
                    for key, value in filter_dict.items()
                ]} if filter_dict else None
            }
        )
        
        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(retriever, self.document_chain)
        
        # Convert chat history to langchain format
        messages = []
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
        
        # Invoke chain
        response = await retrieval_chain.ainvoke({
            "input": message,
            "chat_history": messages
        })
        
        # Format response
        sources = []
        for doc in response.get("context", []):
            sources.append({
                "content": doc.page_content[:200] + "...",  # Preview
                "metadata": doc.metadata
            })
        
        return {
            "answer": response["answer"],
            "sources": sources,
            "question": message
        }
    
    async def search_documents(
        self,
        query: str,
        folder_id: Optional[str] = None,
        file_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents without generating an answer
        """
        # Build filter
        filter_dict = {}
        if folder_id:
            filter_dict["folder_id"] = folder_id
        if file_id:
            filter_dict["file_id"] = file_id
        
        # Search documents
        results = await self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter_dict=filter_dict
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            })
        
        return formatted_results