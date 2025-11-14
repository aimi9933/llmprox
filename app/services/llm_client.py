import asyncio
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.schemas import LLMProvider
import structlog

logger = structlog.get_logger()


class LLMClient:
    def __init__(self, provider: LLMProvider = LLMProvider.OLLAMA):
        self.provider = provider
        self.base_url = self._get_base_url()
        self.headers = self._get_headers()
        
    def _get_base_url(self) -> str:
        """获取LLM服务的基础URL"""
        if self.provider == LLMProvider.OLLAMA:
            return settings.ollama_base_url
        elif self.provider == LLMProvider.OPENAI:
            return settings.openai_base_url or "https://api.openai.com/v1"
        elif self.provider == LLMProvider.LM_STUDIO:
            return "http://localhost:1234/v1"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        
        if self.provider == LLMProvider.OPENAI and settings.openai_api_key:
            headers["Authorization"] = f"Bearer {settings.openai_api_key}"
            
        return headers
    
    async def generate_completion(self, prompt: str, model: Optional[str] = None, 
                                 max_tokens: int = 256, temperature: float = 0.7) -> str:
        """生成文本补全"""
        if not model:
            model = settings.default_model
            
        async with httpx.AsyncClient() as client:
            if self.provider == LLMProvider.OLLAMA:
                response = await self._ollama_generate(client, prompt, model, max_tokens, temperature)
            else:
                response = await self._openai_generate(client, prompt, model, max_tokens, temperature)
            
            return response
    
    async def _ollama_generate(self, client: httpx.AsyncClient, prompt: str, 
                              model: str, max_tokens: int, temperature: float) -> str:
        """Ollama生成接口"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except httpx.HTTPError as e:
            logger.error("Ollama API error", error=str(e))
            raise
    
    async def _openai_generate(self, client: httpx.AsyncClient, prompt: str, 
                              model: str, max_tokens: int, temperature: float) -> str:
        """OpenAI兼容接口"""
        url = f"{self.base_url}/completions"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["text"]
            
        except httpx.HTTPError as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def generate_chat_completion(self, messages: List[Dict[str, str]], 
                                     model: Optional[str] = None,
                                     max_tokens: int = 256, temperature: float = 0.7) -> str:
        """生成对话补全"""
        if not model:
            model = settings.default_model
            
        async with httpx.AsyncClient() as client:
            if self.provider == LLMProvider.OLLAMA:
                response = await self._ollama_chat(client, messages, model, max_tokens, temperature)
            else:
                response = await self._openai_chat(client, messages, model, max_tokens, temperature)
            
            return response
    
    async def _ollama_chat(self, client: httpx.AsyncClient, messages: List[Dict[str, str]], 
                          model: str, max_tokens: int, temperature: float) -> str:
        """Ollama对话接口"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
            
        except httpx.HTTPError as e:
            logger.error("Ollama chat API error", error=str(e))
            raise
    
    async def _openai_chat(self, client: httpx.AsyncClient, messages: List[Dict[str, str]], 
                          model: str, max_tokens: int, temperature: float) -> str:
        """OpenAI对话接口"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except httpx.HTTPError as e:
            logger.error("OpenAI chat API error", error=str(e))
            raise
    
    async def list_models(self) -> List[str]:
        """列出可用模型"""
        async with httpx.AsyncClient() as client:
            if self.provider == LLMProvider.OLLAMA:
                url = f"{self.base_url}/api/tags"
                try:
                    response = await client.get(url, headers=self.headers, timeout=10.0)
                    response.raise_for_status()
                    
                    result = response.json()
                    return [model["name"] for model in result.get("models", [])]
                    
                except httpx.HTTPError as e:
                    logger.error("Failed to list Ollama models", error=str(e))
                    return []
            else:
                # OpenAI兼容接口通常不支持列出模型
                return [settings.default_model]
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with httpx.AsyncClient() as client:
                if self.provider == LLMProvider.OLLAMA:
                    url = f"{self.base_url}/api/tags"
                else:
                    url = f"{self.base_url}/models"
                
                response = await client.get(url, headers=self.headers, timeout=5.0)
                return response.status_code == 200
                
        except httpx.HTTPError:
            return False


# 全局LLM客户端实例
llm_client = LLMClient(LLMProvider(settings.llm_provider))