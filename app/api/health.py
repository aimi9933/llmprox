from fastapi import APIRouter, HTTPException
from app.services.llm_client import llm_client
from app.core.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """健康检查接口"""
    try:
        # 检查LLM服务状态
        llm_healthy = await llm_client.health_check()
        
        status = {
            "status": "healthy" if llm_healthy else "degraded",
            "version": settings.api_version,
            "llm_provider": settings.llm_provider,
            "llm_status": "connected" if llm_healthy else "disconnected",
            "timestamp": "2024-01-01T00:00:00Z"  # 简化的时间戳
        }
        
        return status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/models")
async def list_models():
    """列出可用的LLM模型"""
    try:
        models = await llm_client.list_models()
        
        return {
            "provider": settings.llm_provider,
            "models": models,
            "default_model": settings.default_model
        }
        
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """获取服务配置信息"""
    return {
        "api_version": settings.api_version,
        "llm_provider": settings.llm_provider,
        "default_model": settings.default_model,
        "max_context_length": settings.max_context_length,
        "max_chunk_size": settings.max_chunk_size,
        "similarity_threshold": settings.similarity_threshold,
        "supported_extensions": settings.supported_extensions
    }