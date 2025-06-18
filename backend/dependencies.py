from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from config import config

# Global variables for lazy loading
_supabase = None
_embeddings = None
_llm = None
_qdrant_client = None
_sentence_model = None


def _get_supabase():
    global _supabase
    if _supabase is None:
        _supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _supabase


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            _embeddings = OpenAIEmbeddings(api_key=config.OPENAI_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI embeddings: {e}")
            print("OpenAI features will not be available. Using local embeddings only.")
            # Return None so the chat service can handle the fallback
            return None
    return _embeddings


def _get_llm():
    global _llm
    if _llm is None:
        try:
            if not config.OPENAI_API_KEY:
                print("Warning: No OpenAI API key found. OpenAI features will not be available.")
                return None
            _llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.LLM_MODEL)
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI LLM: {e}")
            print("OpenAI features will not be available. Using local model only.")
            return None
    return _llm


def _get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    return _qdrant_client


def _get_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        from sentence_transformers import SentenceTransformer
        _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sentence_model


def get_supabase() -> Client:
    """Dependency to get Supabase client"""
    return _get_supabase()


def get_embeddings():
    """Dependency to get OpenAI embeddings"""
    return _get_embeddings()


def get_llm():
    """Dependency to get ChatOpenAI instance"""
    return _get_llm()


def get_qdrant_client():
    """Dependency to get Qdrant client"""
    return _get_qdrant_client()


def get_sentence_model():
    """Dependency to get sentence transformer model"""
    return _get_sentence_model() 


