import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    CompletionRequest, CompletionResponse,
    DebugRequest, DebugResponse,
    ContextRequest, ContextResponse
)
from app.services.chunker import SemanticChunker
from app.services.llm_client import llm_client
from app.services.context_manager import context_manager
from app.core.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/code", tags=["code"])


@router.post("/complete", response_model=CompletionResponse)
async def code_completion(request: CompletionRequest):
    """代码补全接口"""
    start_time = time.time()
    
    try:
        # 获取或创建会话
        session_id = context_manager.dialog_memory.get_or_create_session(request.session_id)
        
        # 分块处理当前代码
        chunker = SemanticChunker()
        current_chunks = chunker.chunk_code(
            request.code, request.file_path, request.language
        )
        
        # 构建补全提示
        prompt = _build_completion_prompt(
            request.code, request.cursor_position, 
            request.language, current_chunks
        )
        
        # 获取相关上下文
        context_chunks = await context_manager.get_relevant_context(
            prompt, current_chunks, session_id, max_chunks=3
        )
        
        # 构建完整提示
        full_prompt = _build_full_completion_prompt(prompt, context_chunks)
        
        # 调用LLM生成补全
        suggestions_text = await llm_client.generate_completion(
            full_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # 解析建议
        suggestions = _parse_completion_suggestions(suggestions_text)
        confidence_scores = [0.8] * len(suggestions)  # 简化的置信度
        
        # 记录对话上下文
        await context_manager.add_dialog_context(
            session_id, "user", 
            f"Code completion request for {request.file_path}",
            [chunk.id for chunk in context_chunks]
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return CompletionResponse(
            suggestions=suggestions,
            confidence_scores=confidence_scores,
            context_chunks=context_chunks,
            session_id=session_id,
            response_time_ms=response_time
        )
        
    except Exception as e:
        logger.error("Code completion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug", response_model=DebugResponse)
async def debug_analysis(request: DebugRequest):
    """代码调试分析接口"""
    start_time = time.time()
    
    try:
        # 获取或创建会话
        session_id = context_manager.dialog_memory.get_or_create_session(request.session_id)
        
        # 分块处理代码
        chunker = SemanticChunker()
        code_chunks = chunker.chunk_code(
            request.code, request.file_path, request.language
        )
        
        # 构建调试提示
        prompt = _build_debug_prompt(
            request.code, request.error_message, 
            request.language, code_chunks
        )
        
        # 获取相关上下文
        context_chunks = await context_manager.get_relevant_context(
            prompt, code_chunks, session_id, max_chunks=5
        )
        
        # 构建完整提示
        full_prompt = _build_full_debug_prompt(prompt, context_chunks)
        
        # 调用LLM进行分析
        analysis_text = await llm_client.generate_completion(
            full_prompt,
            max_tokens=512,
            temperature=0.3  # 较低的温度以获得更准确的分析
        )
        
        # 解析分析结果
        analysis, suggestions, fixed_code = _parse_debug_analysis(analysis_text)
        
        # 记录对话上下文
        await context_manager.add_dialog_context(
            session_id, "user",
            f"Debug analysis for {request.file_path}: {request.error_message}",
            [chunk.id for chunk in context_chunks]
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return DebugResponse(
            analysis=analysis,
            suggestions=suggestions,
            fixed_code=fixed_code,
            context_chunks=context_chunks,
            session_id=session_id,
            response_time_ms=response_time
        )
        
    except Exception as e:
        logger.error("Debug analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    """获取代码上下文接口"""
    start_time = time.time()
    
    try:
        # 分块处理代码
        chunker = SemanticChunker()
        chunks = chunker.chunk_code(
            request.code, request.file_path, request.language
        )
        
        # 计算总token数
        total_tokens = sum(chunk.token_count for chunk in chunks)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ContextResponse(
            chunks=chunks[:request.max_chunks],
            total_tokens=total_tokens,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error("Context retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _build_completion_prompt(code: str, cursor_pos: int, 
                           language: str, chunks: list) -> str:
    """构建代码补全提示"""
    lines = code.split('\n')
    current_line = code[:cursor_pos].count('\n')
    
    # 获取光标前后的上下文
    context_start = max(0, current_line - 5)
    context_end = min(len(lines), current_line + 5)
    context_lines = lines[context_start:context_end]
    
    prompt = f"""Complete the following {language} code at the cursor position:

Context:
{chr(10).join(f"{i+context_start+1}: {line}" for i, line in enumerate(context_lines))}

Cursor is at line {current_line + 1}.

Provide 3-5 intelligent code completion suggestions that fit the context and follow best practices for {language}.

Suggestions:"""
    
    return prompt


def _build_full_completion_prompt(base_prompt: str, context_chunks: list) -> str:
    """构建完整的补全提示"""
    if not context_chunks:
        return base_prompt
    
    context_text = "\n\n".join([
        f"Related code from {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}):\n{chunk.content}"
        for chunk in context_chunks[:2]  # 限制上下文长度
    ])
    
    full_prompt = f"""{base_prompt}

Additional Context:
{context_text}

Consider this additional context when providing suggestions."""
    
    return full_prompt


def _build_debug_prompt(code: str, error_message: Optional[str], 
                       language: str, chunks: list) -> str:
    """构建调试提示"""
    prompt = f"""Analyze the following {language} code for potential issues:

```{language}
{code}
```

"""
    
    if error_message:
        prompt += f"Error message: {error_message}\n\n"
    
    prompt += """Provide:
1. Analysis of the issue
2. Specific suggestions to fix it
3. Fixed code (if applicable)

Analysis:"""
    
    return prompt


def _build_full_debug_prompt(base_prompt: str, context_chunks: list) -> str:
    """构建完整的调试提示"""
    if not context_chunks:
        return base_prompt
    
    context_text = "\n\n".join([
        f"Related code from {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}):\n{chunk.content}"
        for chunk in context_chunks[:3]
    ])
    
    full_prompt = f"""{base_prompt}

Additional Context:
{context_text}

Consider this additional context in your analysis."""
    
    return full_prompt


def _parse_completion_suggestions(suggestions_text: str) -> List[str]:
    """解析补全建议"""
    lines = suggestions_text.strip().split('\n')
    suggestions = []
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('//'):
            # 移除可能的前缀（如数字、点号等）
            clean_line = line.lstrip('0123456789.- ')
            if clean_line:
                suggestions.append(clean_line)
    
    # 如果没有解析到建议，返回原始文本
    if not suggestions:
        suggestions = [suggestions_text.strip()]
    
    return suggestions[:5]  # 最多返回5个建议


def _parse_debug_analysis(analysis_text: str) -> tuple[str, List[str], Optional[str]]:
    """解析调试分析结果"""
    lines = analysis_text.split('\n')
    analysis = []
    suggestions = []
    fixed_code = None
    
    current_section = None
    code_lines = []
    
    for line in lines:
        line = line.strip()
        
        if line.lower().startswith('analysis:'):
            current_section = 'analysis'
        elif line.lower().startswith('suggestions:'):
            current_section = 'suggestions'
        elif line.lower().startswith('fixed code:'):
            current_section = 'fixed_code'
        elif line.startswith('```'):
            if current_section == 'fixed_code' and code_lines:
                fixed_code = '\n'.join(code_lines)
                code_lines = []
            current_section = None
        elif current_section == 'analysis':
            if line:
                analysis.append(line)
        elif current_section == 'suggestions':
            if line and line[0].isdigit():
                # 移除数字前缀
                clean_suggestion = line.lstrip('0123456789.- ')
                suggestions.append(clean_suggestion)
            elif line:
                suggestions.append(line)
        elif current_section == 'fixed_code':
            code_lines.append(line)
    
    # 如果没有找到明确的部分，使用整个文本作为分析
    if not analysis and not suggestions:
        analysis = [analysis_text]
    
    return '\n'.join(analysis), suggestions, fixed_code