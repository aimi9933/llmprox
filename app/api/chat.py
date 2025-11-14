import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chunker import SemanticChunker
from app.services.llm_client import llm_client
from app.services.context_manager import context_manager
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """聊天对话接口"""
    start_time = time.time()
    
    try:
        # 获取或创建会话
        session_id = context_manager.dialog_memory.get_or_create_session(request.session_id)
        
        # 构建对话上下文
        context_chunks = []
        if request.context_code and request.file_path and request.language:
            # 如果提供了上下文代码，进行分块
            chunker = SemanticChunker()
            context_chunks = chunker.chunk_code(
                request.context_code, request.file_path, request.language
            )
        
        # 获取历史对话上下文
        context_messages = await context_manager.dialog_memory.get_context_messages(
            session_id, request.message, max_messages=10
        )
        
        # 构建消息列表
        messages = []
        
        # 添加系统提示
        system_prompt = _build_system_prompt(request.language)
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        for msg in context_messages:
            if msg.role in ["user", "assistant"]:
                messages.append({"role": msg.role, "content": msg.content})
        
        # 添加代码上下文（如果有）
        if context_chunks:
            context_text = "\n\n".join([
                f"Code from {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}):\n{chunk.content}"
                for chunk in context_chunks[:3]
            ])
            messages.append({
                "role": "user", 
                "content": f"Current code context:\n{context_text}"
            })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": request.message})
        
        # 调用LLM生成回复
        response_text = await llm_client.generate_chat_completion(
            messages,
            max_tokens=512,
            temperature=0.7
        )
        
        # 记录用户消息
        await context_manager.add_dialog_context(
            session_id, "user", request.message,
            [chunk.id for chunk in context_chunks]
        )
        
        # 记录助手回复
        await context_manager.add_dialog_context(
            session_id, "assistant", response_text,
            [chunk.id for chunk in context_chunks]
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            context_chunks=context_chunks,
            response_time_ms=response_time
        )
        
    except Exception as e:
        logger.error("Chat message failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """获取聊天历史"""
    try:
        if session_id not in context_manager.dialog_memory.sessions:
            return {"messages": [], "session_id": session_id}
        
        messages = context_manager.dialog_memory.sessions[session_id]
        recent_messages = messages[-limit:]
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "context_chunks": msg.context_chunks
                }
                for msg in recent_messages
            ],
            "session_id": session_id,
            "total_messages": len(messages)
        }
        
    except Exception as e:
        logger.error("Failed to get chat history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    try:
        if session_id in context_manager.dialog_memory.sessions:
            del context_manager.dialog_memory.sessions[session_id]
            return {"message": "Session cleared", "session_id": session_id}
        else:
            return {"message": "Session not found", "session_id": session_id}
            
    except Exception as e:
        logger.error("Failed to clear session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """列出所有会话"""
    try:
        sessions = []
        for session_id, messages in context_manager.dialog_memory.sessions.items():
            summary = context_manager.dialog_memory.get_session_summary(session_id)
            sessions.append(summary)
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _build_system_prompt(language: Optional[str] = None) -> str:
    """构建系统提示"""
    base_prompt = """You are an intelligent coding assistant integrated with an IDE. 
You help developers with code completion, debugging, explanation, and best practices.
You have access to relevant code context and conversation history to provide accurate, helpful responses.

Your role is to:
- Provide accurate and helpful coding assistance
- Explain code concepts clearly
- Suggest improvements and best practices
- Help debug and fix issues
- Consider the provided code context in your responses"""

    if language:
        language_specific = f"""

Focus on {language} programming language and its specific:
- Syntax and conventions
- Best practices and patterns
- Common pitfalls and issues
- Standard libraries and frameworks"""
        
        return base_prompt + language_specific
    
    return base_prompt