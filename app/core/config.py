try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from typing import Optional, List
import os


class Settings(BaseSettings):
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "IDE Python Proxy Server"
    api_version: str = "1.0.0"
    
    # LLM Settings
    llm_provider: str = "ollama"  # ollama, openai, lm_studio
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    default_model: str = "codellama"
    
    # Context Management
    max_context_length: int = 8000  # tokens
    chunk_overlap_ratio: float = 0.1
    max_chunks_per_request: int = 10
    
    # Semantic Chunking
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7
    max_chunk_size: int = 2000  # tokens
    
    # Dialog Memory
    max_dialog_history: int = 20
    memory_ttl: int = 3600  # seconds
    
    # File Processing
    supported_extensions: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", 
        ".java", ".cpp", ".c", ".h", ".hpp",
        ".cs", ".go", ".rs", ".php", ".rb"
    ]
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()