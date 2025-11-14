import asyncio
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import structlog
from app.models.schemas import CodeChunk, DialogMessage
from app.core.config import settings
import time
import uuid
from datetime import datetime, timedelta

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self._embedding_cache: Dict[str, List[float]] = {}
        
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        if text in self._embedding_cache:
            return self._embedding_cache[text]
        
        # 在线程池中执行CPU密集型任务
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.model.encode, text
        )
        
        embedding_list = embedding.tolist()
        self._embedding_cache[text] = embedding_list
        return embedding_list
    
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        embedding1 = await self.get_embedding(text1)
        embedding2 = await self.get_embedding(text2)
        
        # 使用余弦相似度
        similarity = cosine_similarity(
            [embedding1], [embedding2]
        )[0][0]
        
        return float(similarity)
    
    async def find_similar_chunks(self, query: str, chunks: List[CodeChunk], 
                                 top_k: int = 5, threshold: float = None) -> List[Tuple[CodeChunk, float]]:
        """找到与查询最相似的代码块"""
        if not threshold:
            threshold = settings.similarity_threshold
        
        if not chunks:
            return []
        
        # 获取查询的嵌入
        query_embedding = await self.get_embedding(query)
        
        # 获取所有块的嵌入
        chunk_embeddings = []
        valid_chunks = []
        
        for chunk in chunks:
            if chunk.embedding:
                chunk_embeddings.append(chunk.embedding)
                valid_chunks.append(chunk)
            else:
                # 如果没有嵌入，计算并缓存
                embedding = await self.get_embedding(chunk.content)
                chunk.embedding = embedding
                chunk_embeddings.append(embedding)
                valid_chunks.append(chunk)
        
        if not chunk_embeddings:
            return []
        
        # 计算相似度
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        
        # 排序并过滤
        chunk_similarity_pairs = list(zip(valid_chunks, similarities))
        chunk_similarity_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # 过滤低于阈值的结果
        filtered_pairs = [
            (chunk, float(sim)) for chunk, sim in chunk_similarity_pairs 
            if sim >= threshold
        ]
        
        return filtered_pairs[:top_k]


class DialogMemory:
    def __init__(self):
        self.sessions: Dict[str, List[DialogMessage]] = {}
        self.embedding_service = EmbeddingService()
        
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """获取或创建会话ID"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        return session_id
    
    async def add_message(self, message: DialogMessage) -> None:
        """添加消息到会话"""
        session_id = message.session_id
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append(message)
        
        # 清理过期消息
        await self._cleanup_old_messages(session_id)
    
    async def get_context_messages(self, session_id: str, 
                                  current_query: Optional[str] = None,
                                  max_messages: int = None) -> List[DialogMessage]:
        """获取上下文相关的消息"""
        if not max_messages:
            max_messages = settings.max_dialog_history
        
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]
        
        if not current_query:
            # 如果没有查询，返回最近的消息
            return messages[-max_messages:]
        
        # 如果有查询，找到相关的历史消息
        relevant_messages = await self._find_relevant_messages(
            current_query, messages, max_messages
        )
        
        return relevant_messages
    
    async def _find_relevant_messages(self, query: str, 
                                    messages: List[DialogMessage],
                                    max_messages: int) -> List[DialogMessage]:
        """找到与查询相关的消息"""
        if not messages:
            return []
        
        # 计算查询与每条消息的相似度
        message_scores = []
        
        for message in messages:
            if message.role == "system":
                # 系统消息总是包含
                message_scores.append((message, 1.0))
            else:
                similarity = await self.embedding_service.compute_similarity(
                    query, message.content
                )
                message_scores.append((message, similarity))
        
        # 按相似度和时间排序
        message_scores.sort(key=lambda x: (x[1], x[0].timestamp), reverse=True)
        
        # 返回最相关的消息
        relevant_messages = [msg for msg, _ in message_scores[:max_messages]]
        
        # 按时间重新排序
        relevant_messages.sort(key=lambda x: x.timestamp)
        
        return relevant_messages
    
    async def _cleanup_old_messages(self, session_id: str) -> None:
        """清理过期消息"""
        if session_id not in self.sessions:
            return
        
        messages = self.sessions[session_id]
        cutoff_time = datetime.now() - timedelta(seconds=settings.memory_ttl)
        
        # 保留最近的消息和系统消息
        filtered_messages = [
            msg for msg in messages 
            if msg.timestamp > cutoff_time or msg.role == "system"
        ]
        
        self.sessions[session_id] = filtered_messages
    
    def get_session_summary(self, session_id: str) -> Dict[str, any]:
        """获取会话摘要"""
        if session_id not in self.sessions:
            return {}
        
        messages = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "last_activity": messages[-1].timestamp if messages else None,
            "roles": list(set(msg.role for msg in messages)),
        }


class ContextManager:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.dialog_memory = DialogMemory()
        
    async def get_relevant_context(self, query: str, code_chunks: List[CodeChunk],
                                  session_id: Optional[str] = None,
                                  max_chunks: int = 5) -> List[CodeChunk]:
        """获取相关的上下文代码块"""
        start_time = time.time()
        
        # 找到相似的代码块
        similar_chunks = await self.embedding_service.find_similar_chunks(
            query, code_chunks, top_k=max_chunks
        )
        
        # 获取对话上下文
        if session_id:
            context_messages = await self.dialog_memory.get_context_messages(
                session_id, query
            )
            
            # 从对话历史中提取相关的代码块ID
            dialog_chunk_ids = set()
            for msg in context_messages:
                dialog_chunk_ids.update(msg.context_chunks)
            
            # 优先选择对话中出现过的代码块
            dialog_chunks = [
                chunk for chunk in code_chunks 
                if chunk.id in dialog_chunk_ids
            ]
            
            if dialog_chunks:
                dialog_similar = await self.embedding_service.find_similar_chunks(
                    query, dialog_chunks, top_k=max_chunks // 2
                )
                similar_chunks.extend(dialog_similar)
        
        # 去重并限制数量
        seen_chunks = set()
        unique_chunks = []
        
        for chunk, _ in similar_chunks:
            if chunk.id not in seen_chunks:
                seen_chunks.add(chunk.id)
                unique_chunks.append(chunk)
        
        processing_time = (time.time() - start_time) * 1000
        logger.info("Context retrieval completed", 
                   chunks_found=len(unique_chunks),
                   processing_time_ms=processing_time)
        
        return unique_chunks[:max_chunks]
    
    async def add_dialog_context(self, session_id: str, role: str, 
                                content: str, context_chunk_ids: List[str] = None) -> None:
        """添加对话上下文"""
        message = DialogMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            session_id=session_id,
            context_chunks=context_chunk_ids or []
        )
        
        await self.dialog_memory.add_message(message)


# 全局上下文管理器实例
context_manager = ContextManager()