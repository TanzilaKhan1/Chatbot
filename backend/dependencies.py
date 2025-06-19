from supabase import create_client, Client
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
import google.generativeai as genai
from openai import OpenAI
import requests
from config import config

# Global variables for lazy loading
_supabase = None
_embeddings = None
_llm = None
_qdrant_client = None
_sentence_model = None
_gemini_model = None


def _get_supabase():
    global _supabase
    if _supabase is None:
        _supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _supabase


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            _embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            print(f"Warning: Failed to initialize HuggingFace embeddings: {e}")
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


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        try:
            if not config.GEMINI_API_KEY:
                print("Warning: No Gemini API key found. Gemini features will not be available.")
                return None
            genai.configure(api_key=config.GEMINI_API_KEY)
            # Use the model from config, which should be gemini-2.0-flash
            _gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini: {e}")
            return None
    return _gemini_model


def check_openai_api_key() -> bool:
    """Check if OpenAI API key is valid and has quota"""
    try:
        if not config.OPENAI_API_KEY:
            return False
        
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        # Try a minimal API call to test the key
        try:
            # Use a very small prompt to minimize cost
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            error_str = str(e).lower()
            if 'quota' in error_str or 'insufficient_quota' in error_str or '429' in error_str:
                print(f"OpenAI quota exceeded: {e}")
            elif 'invalid' in error_str or 'incorrect' in error_str:
                print(f"OpenAI API key invalid: {e}")
            else:
                print(f"OpenAI API error: {e}")
            return False
    except Exception as e:
        print(f"OpenAI API key check failed: {e}")
        return False


def check_gemini_api_key() -> bool:
    """Check if Gemini API key is valid"""
    try:
        if not config.GEMINI_API_KEY:
            return False
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        # List available models to verify API key and find supported models
        try:
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            print(f"Available Gemini models: {available_models}")
            
            # Check if our configured model is available
            model_name = f"models/{config.GEMINI_MODEL}"
            if model_name not in available_models:
                print(f"Warning: Configured model {config.GEMINI_MODEL} not available.")
                print(f"Available models: {', '.join([m.replace('models/', '') for m in available_models])}")
                # Try with the first available model
                if available_models:
                    first_model = available_models[0].replace('models/', '')
                    print(f"Trying with {first_model}")
                    model = genai.GenerativeModel(first_model)
                    response = model.generate_content("Hello")
                    return True
                return False
            
            # Test the configured model
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            response = model.generate_content("Hello")
            return True
        except Exception as e:
            print(f"Gemini API error: {e}")
            return False
    except Exception as e:
        print(f"Gemini API key invalid or error: {e}")
        return False


def check_ollama_availability() -> bool:
    """Check if Ollama is running and model is available"""
    try:
        # First check if Ollama is running
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/version", timeout=5)
        if response.status_code != 200:
            print("Ollama is not running")
            return False
        
        # Check if the specific model is available
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            # Check for exact match or base model match
            requested_model = config.OLLAMA_MODEL
            if ':' in requested_model:
                base_model = requested_model.split(':')[0]
            else:
                base_model = requested_model
            
            # Check if model exists (either exact or any version)
            model_exists = any(
                name == requested_model or name.startswith(f"{base_model}:")
                for name in model_names
            )
            
            if not model_exists:
                print(f"Ollama model {requested_model} is not pulled. Available models: {model_names}")
                print(f"Please run: ollama pull {requested_model}")
                return False
            
            # Test the model with a simple request
            test_response = requests.post(
                f"{config.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": requested_model,
                    "prompt": "Hi",
                    "stream": False
                },
                timeout=10
            )
            
            if test_response.status_code == 200:
                return True
            else:
                print(f"Ollama model test failed: {test_response.status_code} - {test_response.text}")
                return False
        return False
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to Ollama at {config.OLLAMA_BASE_URL}. Make sure Ollama is running.")
        return False
    except Exception as e:
        print(f"Ollama availability check failed: {e}")
        return False


def get_supabase() -> Client:
    """Dependency to get Supabase client"""
    return _get_supabase()


def get_embeddings():
    """Dependency to get HuggingFace embeddings"""
    return _get_embeddings()


def get_llm():
    """Dependency to get ChatOpenAI instance"""
    return _get_llm()


def get_qdrant_client():
    """Dependency to get Qdrant client"""
    return _get_qdrant_client()


def get_gemini_model():
    """Dependency to get Gemini model"""
    return _get_gemini_model()


def get_chat_service():
    """Dependency to get ChatService instance"""
    from services.chat_service import ChatService
    return ChatService(
        supabase=_get_supabase(),
        embeddings=_get_embeddings(),
        llm=_get_llm(),
        qdrant_client=_get_qdrant_client(),
        gemini_model=_get_gemini_model()
    )