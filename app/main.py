from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import code, chat, health
import structlog

# 配置日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# 创建FastAPI应用
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="IDE Python Proxy Server - 智能代码上下文管理和LLM集成服务"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定的IDE域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(code.router)
app.include_router(chat.router)
app.include_router(health.router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("IDE Python Proxy Server starting up",
               version=settings.api_version,
               llm_provider=settings.llm_provider)
    
    # 检查LLM连接
    from app.services.llm_client import llm_client
    try:
        is_healthy = await llm_client.health_check()
        if is_healthy:
            logger.info("LLM service connected successfully")
        else:
            logger.warning("LLM service not available")
    except Exception as e:
        logger.error("Failed to connect to LLM service", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("IDE Python Proxy Server shutting down")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error("Unhandled exception",
                path=request.url.path,
                method=request.method,
                error=str(exc))
    
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )