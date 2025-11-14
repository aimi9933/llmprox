from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    LM_STUDIO = "lm_studio"


class CodeChunk(BaseModel):
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    token_count: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}


class DialogMessage(BaseModel):
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    session_id: str
    context_chunks: List[str] = []  # chunk IDs
    metadata: Dict[str, Any] = {}


class CompletionRequest(BaseModel):
    code: str
    file_path: str
    cursor_position: int
    language: str
    context_window: int = 4000
    session_id: Optional[str] = None
    max_tokens: int = 256
    temperature: float = 0.7


class CompletionResponse(BaseModel):
    suggestions: List[str]
    confidence_scores: List[float]
    context_chunks: List[CodeChunk]
    session_id: str
    response_time_ms: float


class DebugRequest(BaseModel):
    code: str
    file_path: str
    error_message: Optional[str] = None
    language: str
    session_id: Optional[str] = None


class DebugResponse(BaseModel):
    analysis: str
    suggestions: List[str]
    fixed_code: Optional[str] = None
    context_chunks: List[CodeChunk]
    session_id: str
    response_time_ms: float


class ContextRequest(BaseModel):
    code: str
    file_path: str
    language: str
    max_chunks: int = 5
    similarity_threshold: float = 0.7


class ContextResponse(BaseModel):
    chunks: List[CodeChunk]
    total_tokens: int
    processing_time_ms: float


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_code: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_chunks: List[CodeChunk]
    response_time_ms: float