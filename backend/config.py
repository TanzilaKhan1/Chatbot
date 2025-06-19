import os
from pathlib import Path
from dotenv import load_dotenv


# Set tokenizer parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv()

class Config:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_BUCKET = "pdf-files"
    
    # Vector Storage Option
    USE_SUPABASE_VECTORS = os.getenv("USE_SUPABASE_VECTORS", "false").lower() == "true"
    
    # Qdrant local
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # Fixed: Added this line
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "pdf_documents")
    
    # OpenAI API (for LLM, not embeddings)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Google Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Local LLM (Ollama)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Embeddings (HuggingFace only)
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = 384  # Fixed dimension for HuggingFace all-MiniLM-L6-v2
    
    # LLM
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Document Processing
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Paths
    TEMP_DIR = Path("temp")
    TEMP_DIR.mkdir(exist_ok=True)

config = Config()